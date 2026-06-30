"""
Standalone inference test for cube detection on Google Coral EdgeTPU.
Falls back to CPU TFLite if EdgeTPU / pycoral is not available.

Usage:
  # After compiling: edgetpu_compiler -s models/cube_detector_best.tflite
  python scripts/test_inference.py

  # Explicit paths
  python scripts/test_inference.py \
      --model  models/cube_detector_best_edgetpu.tflite \
      --images dataset/images/
"""

import sys
import time
import argparse
from pathlib import Path

import cv2
import numpy as np

# -----------------------------------------------------------------------
# Args
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Inference test for cube detector")
parser.add_argument("--model",      type=Path,
                    default=Path("./models/cube_detector_best_edgetpu.tflite"),
                    help="Path to EdgeTPU-compiled .tflite model")
parser.add_argument("--images-dir", type=Path,
                    default=Path("./dataset/images"),
                    help="Directory with test images")
parser.add_argument("--output-dir", type=Path,
                    default=Path("./outputs/inference_test"),
                    help="Where to save annotated output images")
parser.add_argument("--threshold",  type=float, default=0.3,
                    help="Detection score threshold")
args = parser.parse_args()

args.output_dir.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------
# Load interpreter — try Coral, fall back to CPU TFLite
# -----------------------------------------------------------------------

USE_CORAL = False

try:
    from pycoral.utils.edgetpu import make_interpreter
    from pycoral.adapters import detect as coral_detect
    PYCORAL_AVAILABLE = True
    print("[Coral] pycoral found.")
except ImportError:
    PYCORAL_AVAILABLE = False
    print("[Coral] EdgeTPU not available, running on CPU")

if PYCORAL_AVAILABLE and args.model.exists():
    try:
        interpreter = make_interpreter(str(args.model))
        interpreter.allocate_tensors()
        USE_CORAL = True
        print(f"[Coral] Loaded EdgeTPU model: {args.model.name}")
    except Exception as e:
        print(f"[Coral] Failed to load EdgeTPU model ({e}) — falling back to CPU")
        PYCORAL_AVAILABLE = False

if not USE_CORAL:
    import tensorflow as tf

    # Try edgetpu model first (runs on CPU if EdgeTPU unavailable),
    # then fall back to plain .tflite
    cpu_model = args.model if args.model.exists() else \
                Path("./models/cube_detector_best.tflite")

    if not cpu_model.exists():
        sys.exit(
            f"ERROR: No model found.\n"
            f"  Tried: {args.model}\n"
            f"  Tried: ./models/cube_detector_best.tflite\n"
            f"Run training first: python scripts/train.py"
        )

    interpreter = tf.lite.Interpreter(model_path=str(cpu_model))
    interpreter.allocate_tensors()
    print(f"[CPU]   Loaded TFLite model: {cpu_model.name}")

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()
INPUT_SIZE     = input_details[0]['shape'][1]   # e.g. 320
print(f"  Input tensor: {input_details[0]['shape']}  dtype={input_details[0]['dtype'].__name__}")

# -----------------------------------------------------------------------
# Preprocessing
# -----------------------------------------------------------------------

def preprocess(img_bgr: np.ndarray) -> np.ndarray:
    """Resize to INPUT_SIZE and convert to uint8 RGB."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return cv2.resize(img_rgb, (INPUT_SIZE, INPUT_SIZE)).astype(np.uint8)


def _suffix(detail: dict) -> int:
    """Return integer suffix of a TFLite output tensor name (e.g. ':1' → 1).
    Used to distinguish scores (:1) from classes (:2) when both have shape [1,N].
    """
    try:
        return int(detail.get("name", "").rsplit(":", 1)[-1])
    except ValueError:
        return 999


# -----------------------------------------------------------------------
# CPU TFLite inference
# -----------------------------------------------------------------------

def run_cpu_inference(img_bgr: np.ndarray):
    """Returns (boxes_pixel, scores, inf_ms)."""
    inp = preprocess(img_bgr)[np.newaxis]

    if input_details[0]['dtype'] == np.float32:
        inp = inp.astype(np.float32) / 255.0

    interpreter.set_tensor(input_details[0]['index'], inp)

    t0 = time.perf_counter()
    interpreter.invoke()
    inf_ms = (time.perf_counter() - t0) * 1000

    # Identify output tensors.
    # tflite_model_maker 0.4.x names: :1=scores, :2=classes, :3=boxes, :0=num_det.
    # Both scores and classes have shape [1,N]; pick the one with lower name suffix
    # (:1) to avoid mistaking class IDs (all zeros for single-class) for scores.
    boxes_detail   = None
    shape2_tensors = []
    for d in output_details:
        s = d['shape']
        if len(s) == 3 and s[2] == 4:
            boxes_detail = d
        elif len(s) == 2:
            shape2_tensors.append(d)

    scores_detail = sorted(shape2_tensors, key=_suffix)[0] if shape2_tensors else None

    if boxes_detail is None or scores_detail is None:
        print("  [WARN] Cannot identify output tensors")
        return [], [], inf_ms

    raw_boxes  = interpreter.get_tensor(boxes_detail['index'])[0]   # [N, 4]
    raw_scores = interpreter.get_tensor(scores_detail['index'])[0]  # [N]

    # Dequantize uint8 outputs: float = scale * (q - zero_point)
    if scores_detail['dtype'] == np.uint8:
        sc, zp = scores_detail['quantization']
        scores = sc * (raw_scores.astype(np.float32) - zp)
    else:
        scores = raw_scores.astype(np.float32)

    if boxes_detail['dtype'] == np.uint8:
        sc, zp = boxes_detail['quantization']
        raw_boxes = sc * (raw_boxes.astype(np.float32) - zp)
    else:
        raw_boxes = raw_boxes.astype(np.float32)

    # Boxes: normalized [ymin, xmin, ymax, xmax] → original pixel coords
    h, w = img_bgr.shape[:2]
    boxes_pixel = []
    for ymin, xmin, ymax, xmax in raw_boxes:
        boxes_pixel.append([
            int(xmin * w), int(ymin * h),
            int(xmax * w), int(ymax * h),
        ])

    return boxes_pixel, scores.tolist(), inf_ms


# -----------------------------------------------------------------------
# Coral inference
# -----------------------------------------------------------------------

def run_coral_inference(img_bgr: np.ndarray):
    """Returns (boxes_pixel, scores, inf_ms).

    coral_detect.get_objects() is NOT used here because it assumes a fixed
    positional output-tensor order (boxes/classes/scores/count = 0/1/2/3)
    that our tflite_model_maker model does not follow — it reads num_detections
    as raw uint8 (255) instead of dequantizing to ~25, then crashes with
    IndexError when it tries range(255) on a 25-element scores array.

    The pycoral interpreter is a standard TFLite interpreter under the hood,
    so we can use the same name-suffix tensor identification as run_cpu_inference.
    """
    inp = preprocess(img_bgr)
    if input_details[0]['dtype'] == np.float32:
        inp = inp.astype(np.float32) / 255.0

    interpreter.set_tensor(input_details[0]['index'], inp[np.newaxis])

    t0 = time.perf_counter()
    interpreter.invoke()
    inf_ms = (time.perf_counter() - t0) * 1000

    # Reuse the same tensor-identification logic as run_cpu_inference
    boxes_detail   = None
    shape2_tensors = []
    for d in output_details:
        s = d['shape']
        if len(s) == 3 and s[2] == 4:
            boxes_detail = d
        elif len(s) == 2:
            shape2_tensors.append(d)

    scores_detail = sorted(shape2_tensors, key=_suffix)[0] if shape2_tensors else None

    if boxes_detail is None or scores_detail is None:
        return [], [], inf_ms

    raw_boxes  = interpreter.get_tensor(boxes_detail['index'])[0]
    raw_scores = interpreter.get_tensor(scores_detail['index'])[0]

    if scores_detail['dtype'] == np.uint8:
        sc, zp = scores_detail['quantization']
        scores = sc * (raw_scores.astype(np.float32) - zp)
    else:
        scores = raw_scores.astype(np.float32)

    if boxes_detail['dtype'] == np.uint8:
        sc, zp = boxes_detail['quantization']
        raw_boxes = sc * (raw_boxes.astype(np.float32) - zp)
    else:
        raw_boxes = raw_boxes.astype(np.float32)

    h, w = img_bgr.shape[:2]
    boxes_pixel = []
    for ymin, xmin, ymax, xmax in raw_boxes:
        boxes_pixel.append([
            int(xmin * w), int(ymin * h),
            int(xmax * w), int(ymax * h),
        ])

    return boxes_pixel, scores.tolist(), inf_ms


# -----------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------

exts        = ("*.jpg", "*.jpeg", "*.png")
image_paths = [p for ext in exts for p in sorted(args.images_dir.glob(ext))]

if not image_paths:
    sys.exit(f"ERROR: No images found in {args.images_dir}")

print(f"\nRunning inference on {len(image_paths)} image(s)...")
print(f"  Backend:   {'Google Coral EdgeTPU' if USE_CORAL else 'CPU (TFLite)'}")
print(f"  Threshold: {args.threshold}")
print("-" * 70)

total_ms    = 0.0
total_dets  = 0
n_processed = 0

for img_path in image_paths:
    img_bgr = cv2.imread(str(img_path))
    if img_bgr is None:
        print(f"  [SKIP] Cannot read {img_path.name}")
        continue

    if USE_CORAL:
        all_boxes, all_scores, inf_ms = run_coral_inference(img_bgr)
    else:
        all_boxes, all_scores, inf_ms = run_cpu_inference(img_bgr)

    # Apply confidence threshold (both paths return all 25 raw candidates)
    pairs  = [(b, s) for b, s in zip(all_boxes, all_scores) if s >= args.threshold]
    boxes  = [p[0] for p in pairs]
    scores = [p[1] for p in pairs]

    total_ms   += inf_ms
    total_dets += len(boxes)
    n_processed += 1

    score_str = str([round(s, 2) for s in scores]) if scores else "[]"
    print(f"  {img_path.name:<42} {inf_ms:6.1f} ms  "
          f"{len(boxes)} box(es)  scores: {score_str}")

    # Save annotated image
    out_img = img_bgr.copy()
    for (x1, y1, x2, y2), score in zip(boxes, scores):
        cv2.rectangle(out_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"cube {score:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(out_img, (x1, y1 - th - 6), (x1 + tw + 4, y1), (0, 0, 255), -1)
        cv2.putText(out_img, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    cv2.imwrite(str(args.output_dir / img_path.name), out_img)

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------

print("-" * 70)
if n_processed > 0:
    print(f"Summary:")
    print(f"  Images processed:  {n_processed}")
    print(f"  Total detections:  {total_dets}")
    print(f"  Avg inference:     {total_ms / n_processed:.1f} ms/frame")
    print(f"  Annotated images:  {args.output_dir}/")
else:
    print("No images were processed.")
