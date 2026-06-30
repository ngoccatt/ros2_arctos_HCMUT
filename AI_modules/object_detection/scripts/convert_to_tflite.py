"""
Convert the saved TF SavedModel to TFLite variants.

Mirrors gesture_recognition/convert_to_tflite.py — run this after train.py
if you need to re-export TFLite files without retraining.

Produces:
  models/cube_detector_float32.tflite  — Float32, no quantization (baseline)
  models/cube_detector_int8.tflite     — INT8 fully quantized (EdgeTPU target)

Usage:
  /home/nam/.pyenv/versions/gesture_env/bin/python \
      scripts/convert_to_tflite.py

  # Custom paths
  python scripts/convert_to_tflite.py \
      --saved-model-dir models/saved_model \
      --images-dir      dataset/images/ \
      --output-dir      models/ \
      --image-size      320 \
      --max-samples     200
"""

import os
import sys
import argparse
import numpy as np
import cv2
import tensorflow as tf
from pathlib import Path

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# -----------------------------------------------------------------------
# Args
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Convert TF SavedModel → Float32 and INT8 TFLite"
)
parser.add_argument("--saved-model-dir", type=Path,
                    default=Path("./models/saved_model"),
                    help="Path to the TF SavedModel directory")
parser.add_argument("--images-dir", type=Path,
                    default=Path("./dataset/images"),
                    help="Images used to build representative dataset for INT8 calibration")
parser.add_argument("--output-dir", type=Path,
                    default=Path("./models"),
                    help="Directory to write .tflite files")
parser.add_argument("--image-size",  type=int, default=320)
parser.add_argument("--max-samples", type=int, default=200,
                    help="Max calibration images for INT8 representative dataset")
args = parser.parse_args()

args.output_dir.mkdir(parents=True, exist_ok=True)

if not args.saved_model_dir.exists():
    sys.exit(
        f"ERROR: SavedModel not found at {args.saved_model_dir}\n"
        f"Run train.py first: python scripts/train.py --epochs 50"
    )

# -----------------------------------------------------------------------
# Representative dataset for INT8 calibration
# -----------------------------------------------------------------------

def build_representative_dataset(images_dir: Path, image_size: int, max_samples: int):
    """Yields normalised float32 images from the training set."""
    exts   = ("*.jpg", "*.jpeg", "*.png")
    paths  = [p for ext in exts for p in sorted(images_dir.glob(ext))][:max_samples]

    if not paths:
        sys.exit(f"ERROR: No images found in {images_dir}")

    print(f"  Using {len(paths)} images for INT8 calibration")

    def generator():
        for p in paths:
            img = cv2.imread(str(p))
            if img is None:
                continue
            img = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
                             (image_size, image_size))
            yield [np.expand_dims(img.astype(np.float32) / 255.0, axis=0)]

    return generator

# -----------------------------------------------------------------------
# Convert
# -----------------------------------------------------------------------

print(f"Loading SavedModel from {args.saved_model_dir} ...")

# ---- Float32 TFLite (no quantization) -----------------------------------
print("\n[1/2] Converting → Float32 TFLite ...")
converter = tf.lite.TFLiteConverter.from_saved_model(str(args.saved_model_dir))
float32_model = converter.convert()

float32_path = args.output_dir / "cube_detector_float32.tflite"
with open(float32_path, "wb") as f:
    f.write(float32_model)
print(f"  Saved: {float32_path}  ({len(float32_model)/1024/1024:.1f} MB)")

# ---- INT8 TFLite (full integer quantization) ----------------------------
print("\n[2/2] Converting → INT8 TFLite (full integer quantization) ...")
converter = tf.lite.TFLiteConverter.from_saved_model(str(args.saved_model_dir))
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = build_representative_dataset(
    args.images_dir, args.image_size, args.max_samples
)
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.uint8
converter.inference_output_type = tf.uint8

int8_model = converter.convert()

int8_path = args.output_dir / "cube_detector_int8.tflite"
with open(int8_path, "wb") as f:
    f.write(int8_model)
print(f"  Saved: {int8_path}  ({len(int8_model)/1024/1024:.1f} MB)")

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------

print("\n" + "=" * 50)
print("Conversion complete!")
print(f"  Float32: {float32_path.name:40s} {len(float32_model)/1024/1024:.1f} MB")
print(f"  INT8:    {int8_path.name:40s} {len(int8_model)/1024/1024:.1f} MB")
size_reduction = (1 - len(int8_model) / len(float32_model)) * 100
print(f"  Size reduction from quantization: {size_reduction:.1f}%")
print()
print("Next steps:")
print("  1. Compare accuracy:  python scripts/compare_raw_vs_tflite.py")
print("  2. Compile EdgeTPU:   edgetpu_compiler -s models/cube_detector_int8.tflite")
print("=" * 50)
