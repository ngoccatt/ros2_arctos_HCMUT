#!/usr/bin/env python3
"""
inspection_inference_backend.py

Runs under Python 3.9.17 (gesture_env) to support TensorFlow / pycoral (EdgeTPU).
Continuously reads from the camera, runs MobileNetV2 binary classification (PASS/FAIL),
displays an OpenCV window, and outputs one JSON line per frame to stdout.

The parent ROS2 node (inspection_node.py, Python 3.10) reads these JSON lines
via a subprocess stdout pipe.

Usage:
    python inspection_inference_backend.py \
        --mode cpu --model /path/to/inspection_model_int8.tflite \
        --metadata /path/to/model_metadata.json [--camera-id 0]

    python inspection_inference_backend.py \
        --mode edgetpu --model /path/to/inspection_model_int8_edgetpu.tflite \
        --metadata /path/to/model_metadata.json

    python inspection_inference_backend.py \
        --mode keras --model /path/to/best_model.h5 \
        --metadata /path/to/model_metadata.json
"""

import sys
import os
import json
import signal
import argparse
import time
import numpy as np
import cv2


def _find_camera():
    """Auto-detect UGREEN webcam; fall back to first available device."""
    import glob
    prefer = ("ugreen", "ultra hd", "4k")
    for p in sorted(glob.glob("/sys/class/video4linux/video*/name")):
        try:
            name = open(p).read().strip().lower()
            idx = int(os.path.basename(os.path.dirname(p)).replace("video", ""))
        except Exception:
            continue
        if any(k in name for k in prefer):
            return idx
    for idx in range(8):
        c = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if c.isOpened():
            c.release()
            return idx
    return None


def main():
    parser = argparse.ArgumentParser(description="Visual inspection inference backend (Python 3.9)")
    parser.add_argument("--mode", choices=["edgetpu", "cpu", "keras"], required=True,
                        help="Inference backend")
    parser.add_argument("--model", required=True,
                        help="Path to model (.tflite for edgetpu/cpu, .h5 for keras)")
    parser.add_argument("--metadata", required=True,
                        help="Path to model_metadata.json")
    parser.add_argument("--camera-id", type=int, default=None,
                        help="OpenCV camera device index (auto-detect if omitted)")
    parser.add_argument("--zoom", type=float, default=1.0,
                        help="Digital center-crop zoom factor (e.g. 2.0 = 2x). "
                             "Crops the centre 1/zoom of the frame before inference.")
    parser.add_argument("--fail-threshold", type=float, default=0.5,
                        help="Minimum FAIL score required to predict FAIL (default 0.5 = argmax). "
                             "Raise to 0.60-0.70 to reduce false rejections.")
    parser.add_argument("--save-frames", type=str, default=None,
                        help="Directory to save every frame fed into the model. "
                             "Filename: frame_<timestamp>_<LABEL>_<conf>.jpg")
    args = parser.parse_args()

    # ── Load metadata ─────────────────────────────────────────────────────────
    with open(args.metadata) as f:
        meta = json.load(f)
    class_names = meta["class_names"]   # ["FAIL", "PASS"]
    img_size = tuple(meta["image_size"])  # (224, 224)

    # ── Load model ────────────────────────────────────────────────────────────
    if args.mode == "keras":
        import tensorflow as tf
        model = tf.keras.models.load_model(args.model)
        print(f"[backend] Keras model loaded: {args.model}", file=sys.stderr, flush=True)

        def preprocess(frame):
            img = cv2.resize(frame, img_size)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return np.expand_dims(img / 255.0, axis=0).astype(np.float32)

        def run_inference(frame):
            t0 = time.perf_counter()
            output = model.predict(preprocess(frame), verbose=0)[0]
            latency_ms = (time.perf_counter() - t0) * 1000
            # class_names = ["FAIL", "PASS"], so index 0 = FAIL, index 1 = PASS
            fail_idx, pass_idx = 0, 1
            pred_idx = fail_idx if output[fail_idx] >= args.fail_threshold else pass_idx
            return class_names[pred_idx], pred_idx, float(output[pred_idx]), latency_ms

    elif args.mode == "edgetpu":
        from pycoral.utils.edgetpu import make_interpreter
        interpreter = make_interpreter(args.model)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        input_index = input_details[0]["index"]
        output_index = output_details[0]["index"]
        input_dtype = input_details[0]["dtype"]
        print(f"[backend] EdgeTPU model loaded: {args.model}", file=sys.stderr, flush=True)

        def preprocess(frame):
            img = cv2.resize(frame, img_size)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.expand_dims(img, axis=0)
            if input_dtype == np.uint8:
                return img.astype(np.uint8)
            return (img / 255.0).astype(np.float32)

        def run_inference(frame):
            interpreter.set_tensor(input_index, preprocess(frame))
            t0 = time.perf_counter()
            interpreter.invoke()
            latency_ms = (time.perf_counter() - t0) * 1000
            output = interpreter.get_tensor(output_index)[0]
            if output_details[0]["dtype"] == np.uint8:
                scale, zero_point = output_details[0]["quantization"]
                output = (output.astype(np.float32) - zero_point) * scale
            fail_idx, pass_idx = 0, 1
            pred_idx = fail_idx if output[fail_idx] >= args.fail_threshold else pass_idx
            return class_names[pred_idx], pred_idx, float(output[pred_idx]), latency_ms

    else:  # cpu tflite
        try:
            import tflite_runtime.interpreter as tflite
            interpreter = tflite.Interpreter(model_path=args.model)
        except ImportError:
            import tensorflow as tf
            interpreter = tf.lite.Interpreter(model_path=args.model)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        input_index = input_details[0]["index"]
        output_index = output_details[0]["index"]
        input_dtype = input_details[0]["dtype"]
        print(f"[backend] CPU TFLite model loaded: {args.model}", file=sys.stderr, flush=True)

        def preprocess(frame):
            img = cv2.resize(frame, img_size)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.expand_dims(img, axis=0)
            if input_dtype == np.uint8:
                return img.astype(np.uint8)
            return (img / 255.0).astype(np.float32)

        def run_inference(frame):
            interpreter.set_tensor(input_index, preprocess(frame))
            t0 = time.perf_counter()
            interpreter.invoke()
            latency_ms = (time.perf_counter() - t0) * 1000
            output = interpreter.get_tensor(output_index)[0]
            if output_details[0]["dtype"] == np.uint8:
                scale, zero_point = output_details[0]["quantization"]
                output = (output.astype(np.float32) - zero_point) * scale
            fail_idx, pass_idx = 0, 1
            pred_idx = fail_idx if output[fail_idx] >= args.fail_threshold else pass_idx
            return class_names[pred_idx], pred_idx, float(output[pred_idx]), latency_ms

    # ── Save-frames setup ─────────────────────────────────────────────────────
    save_dir = None
    frame_counter = 0
    if args.save_frames:
        save_dir = os.path.expanduser(args.save_frames)
        os.makedirs(save_dir, exist_ok=True)
        print(f"[backend] Saving frames to: {save_dir}", file=sys.stderr, flush=True)

    # ── Zoom helper ───────────────────────────────────────────────────────────
    zoom_factor = max(1.0, args.zoom)

    def apply_zoom(frame):
        """Center-crop by zoom_factor then scale back to original resolution."""
        if zoom_factor <= 1.0:
            return frame
        h, w = frame.shape[:2]
        crop_h = int(h / zoom_factor)
        crop_w = int(w / zoom_factor)
        y0 = (h - crop_h) // 2
        x0 = (w - crop_w) // 2
        return cv2.resize(frame[y0:y0 + crop_h, x0:x0 + crop_w], (w, h),
                          interpolation=cv2.INTER_LINEAR)

    # ── Open camera ───────────────────────────────────────────────────────────
    cam_idx = args.camera_id if args.camera_id is not None else _find_camera()
    if cam_idx is None:
        print(json.dumps({"error": "No camera found"}), flush=True)
        sys.exit(1)

    cap = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print(json.dumps({"error": f"Cannot open camera id={cam_idx}"}), flush=True)
        sys.exit(1)
    print(f"[backend] Camera opened on index {cam_idx}", file=sys.stderr, flush=True)

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    running = [True]

    def on_signal(sig, frame):
        running[0] = False

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    window_title = f"Visual Inspection [{args.mode.upper()}]"

    # ── Main inference loop ───────────────────────────────────────────────────
    while running[0]:
        capture_time = time.time()   # Unix timestamp of camera grab (for pipeline latency)
        ret, frame = cap.read()
        if not ret:
            break

        frame = apply_zoom(frame)

        # Skip inference if no object is present (flat/empty frame).
        # Grayscale std-dev < 8 means the frame is too uniform to contain an object.
        if np.std(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) < 8.0:
            label, class_id, confidence, latency_ms = "NO_OBJECT", -1, 0.0, 0.0
        else:
            label, class_id, confidence, latency_ms = run_inference(frame)

        # ── Save frame (exact pixels fed into the model) ──────────────────────
        if save_dir is not None:
            frame_counter += 1
            ts = time.strftime("%Y%m%d_%H%M%S")
            fname = f"frame_{ts}_{frame_counter:05d}_{label}_{confidence:.2f}.jpg"
            cv2.imwrite(os.path.join(save_dir, fname), frame)

        # Overlay on frame
        color = (0, 200, 0) if label == "PASS" else (0, 0, 220)
        overlay = f"{label}  {confidence:.1%}  {latency_ms:.0f}ms"
        cv2.putText(frame, overlay, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        if label == "FAIL":
            cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1),
                          (0, 0, 220), 3)

        cv2.imshow(window_title, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # Output JSON to stdout — one line per frame
        print(json.dumps({
            "label":             label,
            "class_id":          class_id,
            "confidence":        confidence,
            "latency_ms":        latency_ms,
            "capture_time_unix": capture_time,
        }), flush=True)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
