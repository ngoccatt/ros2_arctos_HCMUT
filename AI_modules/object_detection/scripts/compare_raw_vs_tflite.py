"""
Compare Float32 TFLite vs INT8 TFLite vs EdgeTPU on the held-out test set.

Mirrors gesture_recognition/compare_raw_vs_tflite.py.
Measures accuracy loss from INT8 quantization AND verifies that the
EdgeTPU-compiled model produces the same results as the INT8 CPU model.

Outputs:
  results/compare_results.json  — full metrics for all three models
  (table printed to stdout)

Usage:
  /home/nam/.pyenv/versions/gesture_env/bin/python \
      scripts/compare_raw_vs_tflite.py

  # Without Coral connected (skips EdgeTPU column automatically)
  python scripts/compare_raw_vs_tflite.py --no-edgetpu

  # Custom paths
  python scripts/compare_raw_vs_tflite.py \
      --float32-model  models/cube_detector_float32.tflite \
      --int8-model     models/cube_detector_int8.tflite \
      --edgetpu-model  models/cube_detector_int8_edgetpu.tflite \
      --test-dir       outputs/voc_split/test \
      --output         results/compare_results.json
"""

import os
import sys
import json
import time
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import cv2
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# -----------------------------------------------------------------------
# Args
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Compare Float32 / INT8 / EdgeTPU TFLite detection accuracy"
)
parser.add_argument("--float32-model",  type=Path,
                    default=Path("./models/cube_detector_float32.tflite"))
parser.add_argument("--int8-model",     type=Path,
                    default=Path("./models/cube_detector_int8.tflite"))
parser.add_argument("--edgetpu-model",  type=Path,
                    default=Path("./models/cube_detector_int8_edgetpu.tflite"))
parser.add_argument("--test-dir",       type=Path,
                    default=Path("./outputs/voc_split/test"),
                    help="Directory with images/ and annotations/ sub-folders")
parser.add_argument("--output",         type=Path,
                    default=Path("./results/compare_results.json"))
parser.add_argument("--iou-thresh",     type=float, default=0.50)
parser.add_argument("--conf-thresh",    type=float, default=0.50)
parser.add_argument("--no-edgetpu",     action="store_true",
                    help="Skip EdgeTPU evaluation (use when Coral is not connected)")
args = parser.parse_args()

Path(args.output).parent.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------
# Coral availability check
# -----------------------------------------------------------------------

CORAL_AVAILABLE = False
if not args.no_edgetpu:
    try:
        from pycoral.utils.edgetpu import make_interpreter as _make_edgetpu
        CORAL_AVAILABLE = True
    except ImportError:
        print("[Coral] pycoral not found — EdgeTPU column will be skipped.")

# -----------------------------------------------------------------------
# Load test items
# -----------------------------------------------------------------------

test_img_dir = args.test_dir / "images"
test_ann_dir = args.test_dir / "annotations"

if not test_ann_dir.exists():
    sys.exit(
        f"ERROR: test split not found at {args.test_dir}\n"
        f"Run train.py first to create the split."
    )

test_items = []
for xml_path in sorted(test_ann_dir.glob("*.xml")):
    img_path = test_img_dir / (xml_path.stem + ".jpg")
    if not img_path.exists():
        img_path = test_img_dir / (xml_path.stem + ".png")
    if img_path.exists():
        test_items.append((img_path, xml_path))

if not test_items:
    sys.exit(f"ERROR: No annotated images found in {args.test_dir}")

print(f"Test set:       {len(test_items)} images")
print(f"IoU threshold:  {args.iou_thresh}")
print(f"Conf threshold: {args.conf_thresh}")

# -----------------------------------------------------------------------
# Tensor identification
# -----------------------------------------------------------------------

def _name_suffix(detail: dict) -> int:
    """Return integer suffix of 'StatefulPartitionedCall:N'; fallback 999.
    Scores = :1, Classes = :2 — picking :1 avoids confusing class IDs for scores.
    """
    try:
        return int(detail.get("name", "").rsplit(":", 1)[-1])
    except ValueError:
        return 999


def build_interpreter(model_path: Path, use_edgetpu: bool = False):
    """Create a TFLite interpreter, optionally routing to Coral EdgeTPU."""
    if use_edgetpu:
        interp = _make_edgetpu(str(model_path))
    else:
        interp = tf.lite.Interpreter(model_path=str(model_path))
    interp.allocate_tensors()
    return interp


# -----------------------------------------------------------------------
# Inference (shared by CPU and EdgeTPU paths)
# -----------------------------------------------------------------------

def run_inference(interpreter, img_bgr: np.ndarray, input_size: int):
    """Run one image; return (boxes_pixel, scores).
    Works for float32, INT8 CPU, and INT8 EdgeTPU interpreters.
    Identifies tensors by name suffix to avoid confusing scores (:1) with
    classes (:2) — both have shape [1, N] in this model.
    """
    input_det  = interpreter.get_input_details()[0]
    output_det = interpreter.get_output_details()

    img = cv2.resize(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB),
                     (input_size, input_size))

    if input_det['dtype'] == np.uint8:
        inp = img.astype(np.uint8)[np.newaxis]
    else:
        inp = (img / 255.0).astype(np.float32)[np.newaxis]

    interpreter.set_tensor(input_det['index'], inp)
    interpreter.invoke()

    shape3 = [d for d in output_det if len(d['shape']) == 3 and d['shape'][2] == 4]
    shape2 = [d for d in output_det if len(d['shape']) == 2]

    if not shape3 or not shape2:
        return [], []

    boxes_det  = shape3[0]
    scores_det = sorted(shape2, key=_name_suffix)[0]

    raw_boxes  = interpreter.get_tensor(boxes_det['index'])[0]
    raw_scores = interpreter.get_tensor(scores_det['index'])[0]

    if scores_det['dtype'] == np.uint8:
        sc, zp = scores_det['quantization']
        scores = sc * (raw_scores.astype(np.float32) - zp)
    else:
        scores = raw_scores.astype(np.float32)

    if boxes_det['dtype'] == np.uint8:
        sc, zp = boxes_det['quantization']
        raw_boxes = sc * (raw_boxes.astype(np.float32) - zp)
    else:
        raw_boxes = raw_boxes.astype(np.float32)

    h, w = img_bgr.shape[:2]
    boxes_pixel = []
    for ymin, xmin, ymax, xmax in raw_boxes:
        boxes_pixel.append([int(xmin*w), int(ymin*h), int(xmax*w), int(ymax*h)])

    return boxes_pixel, scores.tolist()


def compute_iou(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2-ix1) * max(0, iy2-iy1)
    if inter == 0:
        return 0.0
    return inter / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter)


# -----------------------------------------------------------------------
# Evaluate one model on the full test set
# -----------------------------------------------------------------------

def evaluate_model(model_path: Path, label: str, use_edgetpu: bool = False):
    print(f"\n{'='*55}")
    print(f"Evaluating: {label}")
    print(f"  File: {model_path.name}")
    print(f"{'='*55}")

    if not model_path.exists():
        print(f"  [SKIP] File not found: {model_path}")
        return None

    if use_edgetpu and not CORAL_AVAILABLE:
        print("  [SKIP] Coral not available.")
        return None

    try:
        interp = build_interpreter(model_path, use_edgetpu=use_edgetpu)
    except Exception as e:
        print(f"  [SKIP] Failed to load model: {e}")
        return None

    input_size   = interp.get_input_details()[0]['shape'][1]
    total_tp = total_fp = total_fn = 0
    total_inf_ms = 0.0

    for img_path, xml_path in test_items:
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            continue

        tree = ET.parse(str(xml_path))
        gt_boxes = []
        for obj in tree.getroot().findall("object"):
            bb = obj.find("bndbox")
            gt_boxes.append([
                int(bb.find("xmin").text), int(bb.find("ymin").text),
                int(bb.find("xmax").text), int(bb.find("ymax").text),
            ])

        t0 = time.perf_counter()
        pred_boxes, pred_scores = run_inference(interp, img_bgr, input_size)
        total_inf_ms += (time.perf_counter() - t0) * 1000

        pred_boxes = [b for b, s in zip(pred_boxes, pred_scores)
                      if s >= args.conf_thresh]

        matched_gt = set()
        tp = fp = 0
        for pb in pred_boxes:
            best_iou, best_idx = 0.0, -1
            for gi, gb in enumerate(gt_boxes):
                if gi in matched_gt:
                    continue
                iou = compute_iou(pb, gb)
                if iou > best_iou:
                    best_iou, best_idx = iou, gi
            if best_iou >= args.iou_thresh and best_idx >= 0:
                tp += 1; matched_gt.add(best_idx)
            else:
                fp += 1
        fn = len(gt_boxes) - len(matched_gt)
        total_tp += tp; total_fp += fp; total_fn += fn

    p   = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    r   = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1  = 2*p*r / (p+r)                   if (p + r)              > 0 else 0.0
    avg = total_inf_ms / len(test_items)

    print(f"  Precision  : {p:.4f}")
    print(f"  Recall     : {r:.4f}")
    print(f"  F1-Score   : {f1:.4f}")
    print(f"  TP={total_tp}  FP={total_fp}  FN={total_fn}")
    print(f"  Avg inference: {avg:.1f} ms/frame")

    return {
        "model":       label,
        "file":        model_path.name,
        "backend":     "EdgeTPU" if use_edgetpu else "CPU",
        "precision":   round(p,   4),
        "recall":      round(r,   4),
        "f1":          round(f1,  4),
        "tp":          total_tp,
        "fp":          total_fp,
        "fn":          total_fn,
        "avg_inf_ms":  round(avg, 2),
        "num_samples": len(test_items),
    }


# -----------------------------------------------------------------------
# Run all three evaluations
# -----------------------------------------------------------------------

results_fp32   = evaluate_model(args.float32_model, "Float32 TFLite  (no quantization, CPU)")
results_int8   = evaluate_model(args.int8_model,    "INT8 TFLite     (quantized, CPU)")
results_edgetpu = evaluate_model(args.edgetpu_model, "INT8 EdgeTPU    (quantized, Coral)",
                                 use_edgetpu=True)

# -----------------------------------------------------------------------
# Comparison table
# -----------------------------------------------------------------------

models = [
    ("Float32 CPU",  results_fp32),
    ("INT8 CPU",     results_int8),
    ("INT8 EdgeTPU", results_edgetpu),
]
# Only include models that were actually evaluated
models = [(name, r) for name, r in models if r is not None]

W = 14   # column width
print(f"\n{'='*(20 + W * len(models))}")
print("ACCURACY COMPARISON")
print(f"{'='*(20 + W * len(models))}")

header = f"{'Metric':<20}" + "".join(f"{name:>{W}}" for name, _ in models)
print(header)
print("-" * (20 + W * len(models)))

for key, row_label in [("precision", "Precision"),
                        ("recall",    "Recall"),
                        ("f1",        "F1-Score")]:
    vals = [r[key] for _, r in models]
    row  = f"  {row_label:<18}" + "".join(f"{v:>{W}.4f}" for v in vals)
    print(row)

print()
inf_row = f"  {'Avg inference':<18}"
for _, r in models:
    inf_row += f"{r['avg_inf_ms']:>{W-2}.1f}ms  "
print(inf_row)

# Speedup vs Float32 if all three present
if results_fp32 and results_edgetpu:
    speedup = results_fp32['avg_inf_ms'] / results_edgetpu['avg_inf_ms']
    print(f"\n  EdgeTPU speedup vs Float32 CPU: {speedup:.1f}×")

print(f"{'='*(20 + W * len(models))}")

# -----------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------

output = {
    "iou_threshold":   args.iou_thresh,
    "conf_threshold":  args.conf_thresh,
    "num_test_images": len(test_items),
    "float32_cpu":     results_fp32,
    "int8_cpu":        results_int8,
    "int8_edgetpu":    results_edgetpu,
}
with open(args.output, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nResults saved to {args.output}")
