# Cube Detection Training Pipeline

Object detection for **3D-printed PLA cubes** (with colored circular stickers)
using **EfficientDet-Lite0**, targeting the **Google Coral USB Accelerator**.

Camera: eye-in-hand on Denso VS-6577E — inference runs once at robot home position.
Output: bounding box `(x, y, w, h)` of the cube.

---

## Project Structure

```
cube_detection_training/
├── dataset/
│   ├── images/           ← all raw images (all phases mixed)
│   └── annotations/      ← labelme COCO JSON exports + merged.json
├── scripts/
│   ├── merge_coco.py     ← merge multiple COCO JSONs into one
│   ├── train.py          ← main training pipeline
│   └── test_inference.py ← EdgeTPU / CPU inference test
├── models/               ← trained .tflite models
├── outputs/              ← plots, reports, VOC split dirs
└── README.md
```

---

## Environment

All scripts use the `gesture_env` pyenv environment:

```
/home/nam/.pyenv/versions/gesture_env/bin/python
```

Required packages (already installed):
- `tflite_model_maker == 0.4.3`
- `tensorflow == 2.8.4`
- `opencv-python`
- `pycocotools`

For EdgeTPU inference only (optional):
- `pycoral`  — install via: `pip install pycoral`

---

## Workflow

### Step 1 — Prepare Dataset

1. Photograph the cube at robot home position (varied lighting, angles).
2. Annotate with **labelme** — class name must be `"cube"`.
3. Export each session as COCO JSON from labelme:
   `File → Export JSON (COCO format)`.
4. Place exported JSON files in `dataset/annotations/`.

### Step 2 — Merge COCO JSON Files

```bash
/home/nam/.pyenv/versions/gesture_env/bin/python \
  scripts/merge_coco.py \
  --input-dir dataset/annotations/ \
  --output    dataset/annotations/merged.json
```

Prints: total images and total annotations after merge.

### Step 3 — Train

```bash
/home/nam/.pyenv/versions/gesture_env/bin/python \
  scripts/train.py \
  --epochs     50 \
  --batch-size 8
```

Pipeline:
1. Load `merged.json`
2. Convert COCO → Pascal VOC XML (`outputs/voc_xml_all/`)
3. Split 80 / 20 train / val into `outputs/voc_split/`
4. Train EfficientDet-Lite0 (`train_whole_model=False`)
5. Evaluate → log mAP, AP50, AP75, AR
6. Export INT8-quantized model → `models/cube_detector_best.tflite`
7. Save `outputs/model_metadata.json`
8. Generate outputs (see below)

### Step 4 — Re-generate Outputs Without Retraining

```bash
/home/nam/.pyenv/versions/gesture_env/bin/python \
  scripts/train.py --skip-training
```

Skips training and export; regenerates `training_history.png`,
`detection_report.txt`, and `sample_detections.png` from the existing model.

### Step 5 — Compile for EdgeTPU

Install the EdgeTPU compiler if not already present:
```bash
# https://coral.ai/docs/edgetpu/compiler/
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" \
  | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
sudo apt update && sudo apt install edgetpu-compiler
```

Compile:
```bash
edgetpu_compiler -s models/cube_detector_best.tflite
# Output: models/cube_detector_best_edgetpu.tflite
```

### Step 6 — Test Inference

```bash
/home/nam/.pyenv/versions/gesture_env/bin/python \
  scripts/test_inference.py
```

- Uses EdgeTPU if pycoral is installed and Coral USB is connected.
- Falls back to CPU TFLite automatically.
- Saves annotated images to `outputs/inference_test/`.

---

## Output Files

| File | Description |
|------|-------------|
| `models/cube_detector_best.tflite` | INT8 quantized model |
| `models/cube_detector_best_edgetpu.tflite` | EdgeTPU-compiled model |
| `outputs/model_metadata.json` | Metrics + training config |
| `outputs/training_history.png` | Bar chart: mAP / AP50 / AP75 / AR |
| `outputs/detection_report.txt` | Model info + metrics + deployment steps |
| `outputs/sample_detections.png` | 6 val images with predicted boxes |
| `outputs/inference_test/` | Annotated test images from `test_inference.py` |

---

## Integration with ROS2 Node

Load the model in the pick-and-place node:

```python
import tensorflow as tf
import numpy as np
import cv2

interpreter = tf.lite.Interpreter("models/cube_detector_best_edgetpu.tflite")
interpreter.allocate_tensors()
input_size = interpreter.get_input_details()[0]['shape'][1]  # 320

def detect_cube(img_bgr, threshold=0.5):
    """Returns (x, y, w, h) of highest-confidence detection, or None."""
    img = cv2.resize(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB),
                     (input_size, input_size)).astype(np.uint8)
    interpreter.set_tensor(interpreter.get_input_details()[0]['index'],
                            img[np.newaxis])
    interpreter.invoke()
    # ... parse output tensors (see scripts/train.py: run_inference_tflite)
```

---

## Tips

- **Dataset size**: aim for ≥ 200 images covering all cube orientations and
  lighting conditions typically seen at home position.
- **Annotation**: label only the top face + full cube boundary; a single
  tight bounding box per cube is sufficient.
- **Threshold**: start at 0.5 for production; lower to 0.3 only if false
  negatives are a concern.
- **Re-training**: collect failure cases, re-annotate, add to `dataset/images/`,
  re-export COCO JSON, re-run merge → train.
# cube_detection_training
