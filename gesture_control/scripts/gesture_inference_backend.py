#!/usr/bin/env python3
"""
Gesture inference backend for gesture_control ROS2 package.

Runs under Python 3.9.17 (gesture_env) to support pycoral (EdgeTPU) and tensorflow (CPU).
Outputs JSON lines to stdout — one per inference frame — for the ROS2 recognition node.

Usage:
    python3 gesture_inference_backend.py \
        --mode edgetpu --model /path/to/model.tflite --metadata /path/to/metadata.json
    python3 gesture_inference_backend.py \
        --mode cpu --model /path/to/model.h5 --metadata /path/to/metadata.json
"""

import sys
import os
import json
import signal
import argparse
import time
import cv2


def main():
    parser = argparse.ArgumentParser(description="Gesture inference backend (Python 3.9)")
    parser.add_argument("--mode", choices=["edgetpu", "cpu"], required=True,
                        help="Inference backend: 'edgetpu' uses pycoral, 'cpu' uses tensorflow")
    parser.add_argument("--model", required=True,
                        help="Path to model file (.tflite for edgetpu, .h5 for cpu)")
    parser.add_argument("--metadata", required=True,
                        help="Path to model_metadata.json")
    parser.add_argument("--camera-id", type=int, default=0,
                        help="OpenCV camera device index (default: 0)")
    args = parser.parse_args()

    # Derive AI module directory from model path:
    # model is at .../gesture_recognition/models/<file>
    # AI module dir is .../gesture_recognition/
    ai_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(args.model)))
    sys.path.insert(0, ai_module_dir)

    # Load the appropriate inference class
    if args.mode == "edgetpu":
        from inference_testing import GestureEdgeTPUInference
        inferencer = GestureEdgeTPUInference(args.model, args.metadata)
        window_title = "Gesture Recognition - EdgeTPU"
    else:
        from inference_testing_cpu import GestureCPUInference
        inferencer = GestureCPUInference(args.model, args.metadata)
        window_title = "Gesture Recognition - CPU (FP32)"

    # Open camera
    cap = cv2.VideoCapture(args.camera_id)
    if not cap.isOpened():
        print(json.dumps({"error": f"Cannot open camera id={args.camera_id}"}), flush=True)
        sys.exit(1)

    # Graceful shutdown on SIGTERM (sent by the ROS2 node on shutdown)
    running = [True]

    def on_signal(sig, frame):
        running[0] = False

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    while running[0]:
        capture_time = time.time()  # Unix epoch when frame is grabbed
        ret, frame = cap.read()
        if not ret:
            break

        result = inferencer.infer(frame)

        label   = str(result.get("label", "none"))
        conf    = float(result.get("confidence", 0.0))
        latency = float(result.get("latency_ms", 0.0))

        # JSON is printed BEFORE imshow so the ROS2 pipeline is never blocked
        # if the window manager is slow or the display call takes extra time.
        print(json.dumps({
            "label":             label,
            "class_id":          int(result.get("class_id", -1)),
            "confidence":        conf,
            "latency_ms":        latency,
            "capture_time_unix": capture_time,
        }), flush=True)

        # Live preview window
        overlay_text = f"{label} ({conf * 100:.1f}%) | {latency:.2f} ms"
        cv2.putText(frame, overlay_text, (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
        cv2.imshow(window_title, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
