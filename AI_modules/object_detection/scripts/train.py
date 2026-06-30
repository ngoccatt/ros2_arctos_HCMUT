"""
EfficientDet-Lite0 training pipeline for cube detection.
Targets Google Coral USB Accelerator (EdgeTPU) via INT8 quantization.

Dataset split: 70 / 15 / 15  (train / val / test)
Evaluation:
  - Validation / Test COCO metrics  via model.evaluate()   (AP50, AP75, mAP, AR)
  - Test detection report            via TFLite inference   (Precision, Recall, F1)
    at IoU=0.50 and confidence=0.50  — same approach as reputable applied-robotics
    detection papers (PASCAL VOC protocol, single-class variant)

Saved models (mirrors gesture_recognition module workflow):
  models/saved_model/                  — TF SavedModel  (original; use for fine-tuning
                                          or converting to ONNX / CoreML / etc.)
  models/cube_detector_float32.tflite  — Float32 TFLite (no quantization; baseline
                                          for compare_raw_vs_tflite.py)
  models/cube_detector_int8.tflite     — INT8 TFLite    (EdgeTPU deployment target)

Output files (match gesture_recognition module style):
  outputs/training_history.png    — grouped bar: val vs test metrics (2-subplot)
  outputs/detection_report.txt    — precision/recall/F1 on test set
  outputs/sample_detections.png   — 6 test images with predicted boxes
  outputs/model_metadata.json     — full config + metrics

Usage:
  python scripts/train.py --epochs 50 --batch-size 8
  python scripts/train.py --skip-training          # regenerate outputs only
"""

import os
import sys
import json
import argparse
import shutil
import random
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# -----------------------------------------------------------------------
# Args
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Train EfficientDet-Lite0 for cube detection")
parser.add_argument("--data-dir",      type=Path, default=Path("./dataset"))
parser.add_argument("--output-dir",    type=Path, default=Path("./outputs"))
parser.add_argument("--image-size",    type=int,  default=320)
parser.add_argument("--batch-size",    type=int,  default=8)
parser.add_argument("--epochs",        type=int,  default=50)
parser.add_argument("--skip-training", action="store_true",
                    help="Skip training; regenerate outputs from existing model/metadata")
args = parser.parse_args()

MODELS_DIR    = Path("./models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
args.output_dir.mkdir(parents=True, exist_ok=True)

LABEL_MAP          = {1: "cube"}
SAVED_MODEL_DIR    = MODELS_DIR / "saved_model"
FLOAT32_MODEL_PATH = MODELS_DIR / "cube_detector_float32.tflite"
MODEL_PATH         = MODELS_DIR / "cube_detector_int8.tflite"   # used for evaluation
METADATA_PATH      = args.output_dir / "model_metadata.json"
VOC_SPLIT_DIR      = args.output_dir / "voc_split"
IMAGES_DIR         = args.data_dir / "images"
MERGED_JSON        = args.data_dir / "annotations" / "merged.json"

# Detection evaluation thresholds — match PASCAL VOC standard
IOU_THRESH  = 0.50
CONF_THRESH = 0.50

# -----------------------------------------------------------------------
# COCO JSON → Pascal VOC XML
# -----------------------------------------------------------------------

def coco_to_pascal_voc(coco_json_path: Path, images_dir: Path, xml_out_dir: Path):
    """Convert COCO annotations to Pascal VOC XML files.
    Returns list of (image_path, xml_path) for every successfully converted image.
    """
    xml_out_dir.mkdir(parents=True, exist_ok=True)

    with open(coco_json_path) as f:
        coco = json.load(f)

    ann_by_image: dict = {}
    for ann in coco.get("annotations", []):
        ann_by_image.setdefault(ann["image_id"], []).append(ann)

    converted, skipped = [], 0

    for img_info in coco["images"]:
        img_path = images_dir / img_info["file_name"]
        if not img_path.exists():
            print(f"  [WARN] Missing image: {img_info['file_name']}")
            skipped += 1
            continue

        anns = ann_by_image.get(img_info["id"], [])
        if not anns:
            skipped += 1
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  [WARN] Cannot read: {img_path.name}")
            skipped += 1
            continue
        h, w = img.shape[:2]

        root = ET.Element("annotation")
        ET.SubElement(root, "folder").text   = "images"
        ET.SubElement(root, "filename").text = img_path.name
        ET.SubElement(root, "path").text     = str(img_path.resolve())
        src = ET.SubElement(root, "source")
        ET.SubElement(src, "database").text  = "cube_detection"
        sz  = ET.SubElement(root, "size")
        ET.SubElement(sz,  "width").text     = str(w)
        ET.SubElement(sz,  "height").text    = str(h)
        ET.SubElement(sz,  "depth").text     = "3"
        ET.SubElement(root, "segmented").text = "0"

        valid_boxes = 0
        for ann in anns:
            x, y, bw, bh = ann["bbox"]
            xmin = max(0, int(x));      ymin = max(0, int(y))
            xmax = min(w, int(x + bw)); ymax = min(h, int(y + bh))
            if xmax <= xmin or ymax <= ymin:
                continue
            obj = ET.SubElement(root, "object")
            ET.SubElement(obj, "name").text      = "cube"
            ET.SubElement(obj, "pose").text      = "Unspecified"
            ET.SubElement(obj, "truncated").text = "0"
            ET.SubElement(obj, "difficult").text = "0"
            bb = ET.SubElement(obj, "bndbox")
            ET.SubElement(bb, "xmin").text = str(xmin)
            ET.SubElement(bb, "ymin").text = str(ymin)
            ET.SubElement(bb, "xmax").text = str(xmax)
            ET.SubElement(bb, "ymax").text = str(ymax)
            valid_boxes += 1

        if valid_boxes == 0:
            skipped += 1
            continue

        ET.indent(ET.ElementTree(root), space="  ")
        xml_path = xml_out_dir / f"{img_path.stem}.xml"
        ET.ElementTree(root).write(str(xml_path), encoding="unicode")
        converted.append((img_path, xml_path))

    print(f"  Converted {len(converted)} images ({skipped} skipped)")
    return converted


# -----------------------------------------------------------------------
# 70 / 15 / 15  train / val / test  split
# -----------------------------------------------------------------------

def split_dataset(converted: list, split_dir: Path, seed: int = 42):
    """Split into train/val/test (70/15/15) with symlinked images.

    Three-way split ensures the test set is never seen during training or
    hyperparameter tuning — required for an unbiased final evaluation.
    """
    random.seed(seed)
    items = converted.copy()
    random.shuffle(items)

    n       = len(items)
    n_train = int(n * 0.70)
    n_val   = int(n * 0.15)
    # remaining images go to test (avoids rounding loss)

    splits = {
        "train": items[:n_train],
        "val":   items[n_train : n_train + n_val],
        "test":  items[n_train + n_val :],
    }

    for name, item_list in splits.items():
        img_dir = split_dir / name / "images"
        ann_dir = split_dir / name / "annotations"
        img_dir.mkdir(parents=True, exist_ok=True)
        ann_dir.mkdir(parents=True, exist_ok=True)

        for img_path, xml_path in item_list:
            link = img_dir / img_path.name
            if not link.exists():
                link.symlink_to(img_path.resolve())
            shutil.copy2(xml_path, ann_dir / xml_path.name)

    print(f"  Split → train: {len(splits['train'])}, "
          f"val: {len(splits['val'])}, test: {len(splits['test'])}")
    return splits["train"], splits["val"], splits["test"]


# -----------------------------------------------------------------------
# IoU helper
# -----------------------------------------------------------------------

def compute_iou(box_a, box_b) -> float:
    """Compute IoU between two [x1, y1, x2, y2] boxes."""
    ix1 = max(box_a[0], box_b[0]);  iy1 = max(box_a[1], box_b[1])
    ix2 = min(box_a[2], box_b[2]);  iy2 = min(box_a[3], box_b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return inter / (area_a + area_b - inter)


# -----------------------------------------------------------------------
# TFLite inference helper
# -----------------------------------------------------------------------

def _name_suffix(detail: dict) -> int:
    """Return the integer suffix of a TFLite output tensor name (e.g. ':1' → 1).
    tflite_model_maker names outputs StatefulPartitionedCall:0/1/2/3 where
    :1 = scores, :2 = classes, :3 = boxes, :0 = num_detections.
    Fallback to 999 so unknown tensors sort last.
    """
    try:
        return int(detail.get("name", "").rsplit(":", 1)[-1])
    except ValueError:
        return 999


def run_inference_tflite(interpreter, img_bgr: np.ndarray, input_size: int):
    """Run a single image; return (boxes_pixel, scores).
    Handles all-uint8 outputs (INT8 quantized model) via dequantization.

    Output tensor identification (tflite_model_maker 0.4.x EfficientDet-Lite):
      StatefulPartitionedCall:0  shape=[1]      → num_detections  (ignored)
      StatefulPartitionedCall:1  shape=[1,N]    → scores          ← we want this
      StatefulPartitionedCall:2  shape=[1,N]    → classes         ← NOT this
      StatefulPartitionedCall:3  shape=[1,N,4]  → boxes
    Both :1 and :2 have shape [1,N]; we pick the one with the LOWER name suffix
    (:1) to avoid confusing classes (all-zero class IDs) for confidence scores.
    """
    input_detail   = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()

    img_rgb     = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (input_size, input_size))

    if input_detail['dtype'] == np.uint8:
        inp = img_resized.astype(np.uint8)[np.newaxis]
    else:
        inp = (img_resized / 255.0).astype(np.float32)[np.newaxis]

    interpreter.set_tensor(input_detail['index'], inp)
    interpreter.invoke()

    boxes_detail  = None
    shape2_tensors = []          # all [1, N] tensors — need to pick scores vs classes
    for d in output_details:
        s = d['shape']
        if len(s) == 3 and s[2] == 4:
            boxes_detail = d
        elif len(s) == 2:
            shape2_tensors.append(d)

    if boxes_detail is None or not shape2_tensors:
        return [], []

    # Among [1,N] candidates, the one with the smallest name suffix is scores (:1).
    # Classes has suffix :2. Sorting ascending and taking [0] is robust even if
    # the output_details list happens to be in a different order.
    scores_detail = sorted(shape2_tensors, key=_name_suffix)[0]

    if boxes_detail is None or scores_detail is None:
        return [], []

    raw_boxes  = interpreter.get_tensor(boxes_detail['index'])[0]
    raw_scores = interpreter.get_tensor(scores_detail['index'])[0]

    # Dequantize uint8: float = scale * (q - zero_point)
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

    # Boxes: normalized [ymin, xmin, ymax, xmax] → pixel [x1, y1, x2, y2]
    h_orig, w_orig = img_bgr.shape[:2]
    boxes_pixel = []
    for ymin, xmin, ymax, xmax in raw_boxes:
        boxes_pixel.append([
            int(xmin * w_orig), int(ymin * h_orig),
            int(xmax * w_orig), int(ymax * h_orig),
        ])

    return boxes_pixel, scores.tolist()


# -----------------------------------------------------------------------
# Test-set evaluation: Precision / Recall / F1
# (PASCAL VOC single-class protocol at fixed IoU and confidence threshold)
# -----------------------------------------------------------------------

def evaluate_detection(test_items: list, model_path: Path, input_size: int,
                       conf_thresh: float = CONF_THRESH,
                       iou_thresh: float  = IOU_THRESH):
    """Compute TP/FP/FN on test set using quantized TFLite model.

    Follows the PASCAL VOC matching protocol:
      - Each GT box can be matched at most once.
      - A prediction is TP if its best-matching GT has IoU >= iou_thresh.
      - Unmatched predictions are FP; unmatched GT boxes are FN.

    Returns (precision, recall, f1, tp, fp, fn).
    """
    import tensorflow as tf

    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()

    total_tp = total_fp = total_fn = 0

    for img_path, xml_path in test_items:
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            continue

        # Load ground truth from Pascal VOC XML
        tree = ET.parse(str(xml_path))
        gt_boxes = []
        for obj in tree.getroot().findall("object"):
            bb = obj.find("bndbox")
            gt_boxes.append([
                int(bb.find("xmin").text), int(bb.find("ymin").text),
                int(bb.find("xmax").text), int(bb.find("ymax").text),
            ])

        # Run TFLite inference
        pred_boxes, pred_scores = run_inference_tflite(interpreter, img_bgr, input_size)
        pred_boxes = [b for b, s in zip(pred_boxes, pred_scores) if s >= conf_thresh]

        # Match predictions → ground truth (greedy, highest-IoU first)
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
            if best_iou >= iou_thresh and best_idx >= 0:
                tp += 1
                matched_gt.add(best_idx)
            else:
                fp += 1

        fn = len(gt_boxes) - len(matched_gt)
        total_tp += tp;  total_fp += fp;  total_fn += fn

    p  = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    r  = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r)             if (p + r)              > 0 else 0.0

    return p, r, f1, total_tp, total_fp, total_fn


# -----------------------------------------------------------------------
# Generate output files  (matches gesture_recognition style)
# -----------------------------------------------------------------------

def generate_outputs(val_m: dict, test_m: dict,
                     test_prf: tuple, test_items: list):
    """
    val_m   : COCO metrics on val set   (mAP, AP50, AP75, AR, ...)
    test_m  : COCO metrics on test set  (mAP, AP50, AP75, AR, ...)
    test_prf: (precision, recall, f1, tp, fp, fn) from TFLite on test set
    test_items: list of (img_path, xml_path) for test set
    """
    print("\n[Outputs] Generating report files...")

    precision, recall, f1, tp, fp, fn = test_prf
    n_test = len(test_items)

    # ---- 1. training_history.png  (2-subplot, matches gesture style) ----
    metric_labels = ["AP50", "AP75", "mAP", "AR"]
    val_vals  = [val_m.get("AP50",0), val_m.get("AP75",0),
                 val_m.get("mAP", 0), val_m.get("AR",  0)]
    test_vals = [test_m.get("AP50",0), test_m.get("AP75",0),
                 test_m.get("mAP", 0), test_m.get("AR",  0)]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: validation vs test COCO metrics
    x  = np.arange(len(metric_labels))
    w  = 0.35
    ax = axes[0]
    b1 = ax.bar(x - w/2, val_vals,  w, label="Validation", color="#2196F3", edgecolor="white")
    b2 = ax.bar(x + w/2, test_vals, w, label="Test",        color="#FF9800", edgecolor="white")
    ax.set_xticks(x); ax.set_xticklabels(metric_labels, fontsize=11)
    ax.set_ylim(0, 1.12); ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Validation vs Test Metrics (COCO)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10); ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    for bar, v in list(zip(b1, val_vals)) + list(zip(b2, test_vals)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
                f"{v:.3f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    # Right: test P / R / F1
    ax2    = axes[1]
    labels = ["Precision", "Recall", "F1-Score"]
    vals   = [precision, recall, f1]
    colors = ["#4CAF50", "#9C27B0", "#F44336"]
    bars   = ax2.bar(labels, vals, color=colors, width=0.45, edgecolor="white")
    ax2.set_ylim(0, 1.12); ax2.set_ylabel("Score", fontsize=11)
    ax2.set_title(f"Test Set Detection  (IoU≥{IOU_THRESH}, conf≥{CONF_THRESH})",
                  fontsize=12, fontweight="bold")
    ax2.grid(axis="y", alpha=0.3)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    for bar, v in zip(bars, vals):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
                 f"{v:.4f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.suptitle("Cube Detection — EfficientDet-Lite0", fontsize=13, fontweight="bold")
    plt.tight_layout()
    out = args.output_dir / "training_history.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")

    # ---- 2. detection_report.txt  (mirrors classification_report.txt) ----
    img_sz = val_m.get("image_size", args.image_size)
    out = args.output_dir / "detection_report.txt"
    with open(out, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("CUBE DETECTION MODEL REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Model:        EfficientDet-Lite0 (INT8 quantized)\n")
        f.write(f"Target HW:    Google Coral USB Accelerator\n")
        f.write(f"Image size:   {img_sz}x{img_sz}\n")
        f.write(f"Epochs:       {val_m.get('epochs',       'N/A')}\n")
        f.write(f"Batch size:   {val_m.get('batch_size',   'N/A')}\n")
        f.write(f"Train images: {val_m.get('train_images', 'N/A')}\n")
        f.write(f"Val images:   {val_m.get('val_images',   'N/A')}\n")
        f.write(f"Test images:  {val_m.get('test_images',  'N/A')}\n\n")

        # COCO metrics table
        f.write("-" * 46 + "\n")
        f.write("EVALUATION METRICS  (COCO, IoU averaged 0.50:0.95)\n")
        f.write("-" * 46 + "\n")
        f.write(f"{'':18s}{'Validation':>12}{'Test':>12}\n")
        f.write(f"  {'mAP  (IoU 0.50:0.95)':<18}"
                f"{val_m.get('mAP',  0):>10.4f}"
                f"{test_m.get('mAP',  0):>12.4f}\n")
        f.write(f"  {'AP50 (IoU 0.50)':<18}"
                f"{val_m.get('AP50', 0):>10.4f}"
                f"{test_m.get('AP50', 0):>12.4f}\n")
        f.write(f"  {'AP75 (IoU 0.75)':<18}"
                f"{val_m.get('AP75', 0):>10.4f}"
                f"{test_m.get('AP75', 0):>12.4f}\n")
        f.write(f"  {'AR   (maxDets=100)':<18}"
                f"{val_m.get('AR',   0):>10.4f}"
                f"{test_m.get('AR',   0):>12.4f}\n\n")

        # P / R / F1 table (mirrors sklearn classification_report format)
        f.write("-" * 55 + "\n")
        f.write(f"TEST SET DETECTION REPORT  "
                f"(IoU={IOU_THRESH:.2f}, confidence={CONF_THRESH:.2f})\n")
        f.write("-" * 55 + "\n")
        f.write(f"{'':>16}{'precision':>11}{'recall':>9}"
                f"{'f1-score':>11}{'support':>9}\n\n")
        support = tp + fn   # total ground-truth boxes in test set
        f.write(f"{'cube':>16}{precision:>11.4f}{recall:>9.4f}"
                f"{f1:>11.4f}{support:>9d}\n\n")
        f.write(f"{'micro avg':>16}{precision:>11.4f}{recall:>9.4f}"
                f"{f1:>11.4f}{support:>9d}\n\n")
        f.write(f"  TP: {tp:4d}   FP: {fp:4d}   FN: {fn:4d}\n\n")

        f.write("-" * 46 + "\n")
        f.write("INFERENCE TIME ESTIMATE\n")
        f.write("-" * 46 + "\n")
        f.write("  CPU only (x86):              ~100 ms/frame\n")
        f.write("  CPU (Raspberry Pi 4):         ~300 ms/frame\n")
        f.write("  Google Coral USB (EdgeTPU):    ~15 ms/frame\n")
        f.write("  (runs once per cycle at robot home position)\n\n")
        f.write("-" * 46 + "\n")
        f.write("DEPLOYMENT\n")
        f.write("-" * 46 + "\n")
        f.write("  1. edgetpu_compiler -s models/cube_detector_int8.tflite\n")
        f.write("  2. Output: models/cube_detector_int8_edgetpu.tflite\n")
        f.write("  3. python scripts/compare_raw_vs_tflite.py\n")
        f.write("  4. python scripts/test_inference.py\n")
    print(f"  Saved: {out}")

    # ---- 3. sample_detections.png  (from test set) ----------------------
    if not MODEL_PATH.exists():
        print(f"  [WARN] Model not found at {MODEL_PATH} — skipping sample_detections.png")
        return
    if not test_items:
        print("  [WARN] No test images — skipping sample_detections.png")
        return

    import tensorflow as tf
    print("  Loading TFLite model for sample detections...")
    interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH))
    interpreter.allocate_tensors()
    input_size = interpreter.get_input_details()[0]['shape'][1]

    random.seed(42)
    sample = random.sample(test_items, min(6, len(test_items)))

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for ax, (img_path, xml_path) in zip(axes, sample):
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            ax.axis("off")
            continue

        ax.imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

        # Draw ground truth in green
        tree = ET.parse(str(xml_path))
        for obj in tree.getroot().findall("object"):
            bb = obj.find("bndbox")
            x1,y1 = int(bb.find("xmin").text), int(bb.find("ymin").text)
            x2,y2 = int(bb.find("xmax").text), int(bb.find("ymax").text)
            ax.add_patch(patches.Rectangle((x1, y1), x2-x1, y2-y1,
                linewidth=1.5, edgecolor="#4CAF50", facecolor="none",
                linestyle="--"))

        # Draw predictions in red
        boxes, scores = run_inference_tflite(interpreter, img_bgr, input_size)
        for (x1, y1, x2, y2), score in zip(boxes, scores):
            if score < 0.3:
                continue
            ax.add_patch(patches.Rectangle((x1, y1), x2-x1, y2-y1,
                linewidth=2, edgecolor="#FF3333", facecolor="none"))
            ax.text(x1, max(0, y1 - 4), f"cube {score:.2f}",
                    fontsize=9, fontweight="bold", color="white",
                    bbox=dict(facecolor="#FF3333", alpha=0.85, pad=1, edgecolor="none"))

        ax.set_title(img_path.name, fontsize=7)
        ax.axis("off")

    for j in range(len(sample), 6):
        axes[j].axis("off")

    plt.suptitle("Sample Detections on Test Set  "
                 "(--- green: ground truth  |  red: predicted, threshold=0.3)",
                 fontsize=11, fontweight="bold")
    plt.tight_layout()
    out = args.output_dir / "sample_detections.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


# -----------------------------------------------------------------------
# --skip-training mode
# -----------------------------------------------------------------------

if args.skip_training:
    print("[Skip-training] Loading existing model and metadata...")

    if not METADATA_PATH.exists():
        sys.exit(f"ERROR: metadata not found at {METADATA_PATH}\n"
                 f"Run without --skip-training first.")
    if not MODEL_PATH.exists():
        sys.exit(f"ERROR: model not found at {MODEL_PATH}\n"
                 f"Run without --skip-training first.")

    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    val_m  = {**metadata.get("val_metrics",  {}),
              "epochs": metadata["epochs"], "batch_size": metadata["batch_size"],
              "train_images": metadata["train_images"], "val_images": metadata["val_images"],
              "test_images":  metadata["test_images"],  "image_size": metadata["image_size"]}
    test_m = metadata.get("test_metrics", {})

    # Reconstruct test items from saved split directory
    test_ann_dir = VOC_SPLIT_DIR / "test" / "annotations"
    test_img_dir = VOC_SPLIT_DIR / "test" / "images"

    if test_ann_dir.exists():
        test_items = []
        for xml_path in sorted(test_ann_dir.glob("*.xml")):
            img_path = test_img_dir / (xml_path.stem + ".jpg")
            if not img_path.exists():
                img_path = test_img_dir / (xml_path.stem + ".png")
            if img_path.exists():
                test_items.append((img_path, xml_path))
    else:
        test_items = []
        print("  [WARN] Test split not found — sample_detections.png may be limited")

    # Recompute P/R/F1 from TFLite model on test set
    if test_items and MODEL_PATH.exists():
        import tensorflow as tf
        input_size = tf.lite.Interpreter(model_path=str(MODEL_PATH)) \
                        .get_input_details()[0]['shape'][1]
        print(f"  Evaluating TFLite on {len(test_items)} test images...")
        test_prf = evaluate_detection(test_items, MODEL_PATH, input_size)
    else:
        # Fall back to saved values
        p = test_m.get("precision", 0.0)
        r = test_m.get("recall",    0.0)
        f = test_m.get("f1",        0.0)
        tp = test_m.get("tp", 0)
        fp = test_m.get("fp", 0)
        fn = test_m.get("fn", 0)
        test_prf = (p, r, f, tp, fp, fn)

    generate_outputs(val_m, test_m, test_prf, test_items)
    print("\nDone.")
    sys.exit(0)


# -----------------------------------------------------------------------
# Full training pipeline
# -----------------------------------------------------------------------

print("[1/7] Checking inputs...")

if not MERGED_JSON.exists():
    sys.exit(
        f"ERROR: merged.json not found at {MERGED_JSON}\n"
        f"Run first: python scripts/labelme_to_coco.py"
    )
if not IMAGES_DIR.exists():
    sys.exit(f"ERROR: images directory not found at {IMAGES_DIR}")

print(f"  Dataset: {MERGED_JSON}")
print(f"  Images:  {IMAGES_DIR}")

# -----------------------------------------------------------------------

print("\n[2/7] Converting COCO JSON → Pascal VOC XML...")
xml_all_dir = args.output_dir / "voc_xml_all"
converted   = coco_to_pascal_voc(MERGED_JSON, IMAGES_DIR, xml_all_dir)

if len(converted) < 10:
    sys.exit(f"ERROR: Only {len(converted)} valid images. Need at least 10.")

# -----------------------------------------------------------------------

print("\n[3/7] Splitting dataset 70 / 15 / 15  (seed=42)...")
train_items, val_items, test_items = split_dataset(converted, VOC_SPLIT_DIR)

train_img_dir = VOC_SPLIT_DIR / "train" / "images"
train_ann_dir = VOC_SPLIT_DIR / "train" / "annotations"
val_img_dir   = VOC_SPLIT_DIR / "val"   / "images"
val_ann_dir   = VOC_SPLIT_DIR / "val"   / "annotations"
test_img_dir  = VOC_SPLIT_DIR / "test"  / "images"
test_ann_dir  = VOC_SPLIT_DIR / "test"  / "annotations"

# -----------------------------------------------------------------------

print("\n[4/7] Loading tflite_model_maker DataLoaders...")
from tflite_model_maker import object_detector
from tflite_model_maker.config import ExportFormat, QuantizationConfig

spec = object_detector.EfficientDetLite0Spec()

print("  Loading train data...")
train_data = object_detector.DataLoader.from_pascal_voc(
    images_dir=str(train_img_dir), annotations_dir=str(train_ann_dir),
    label_map=LABEL_MAP)
print(f"  Train: {len(train_data)} samples")

print("  Loading val data...")
val_data = object_detector.DataLoader.from_pascal_voc(
    images_dir=str(val_img_dir), annotations_dir=str(val_ann_dir),
    label_map=LABEL_MAP)
print(f"  Val:   {len(val_data)} samples")

print("  Loading test data...")
test_data = object_detector.DataLoader.from_pascal_voc(
    images_dir=str(test_img_dir), annotations_dir=str(test_ann_dir),
    label_map=LABEL_MAP)
print(f"  Test:  {len(test_data)} samples")

# -----------------------------------------------------------------------

print(f"\n[5/7] Training EfficientDet-Lite0 "
      f"({args.epochs} epochs, batch={args.batch_size})...")
t0 = time.time()

model = object_detector.create(
    train_data,
    model_spec=spec,
    validation_data=val_data,
    epochs=args.epochs,
    batch_size=args.batch_size,
    train_whole_model=False,
)
print(f"  Training complete in {(time.time()-t0)/60:.1f} min")

# -----------------------------------------------------------------------

print("\n[6/7] Evaluating on validation and test sets...")

print("  Evaluating on val set...")
val_eval = model.evaluate(val_data)
print(f"  Val  raw: {val_eval}")

print("  Evaluating on test set...")
test_eval = model.evaluate(test_data)
print(f"  Test raw: {test_eval}")

def extract_coco(ev):
    return {
        "mAP":  round(float(ev.get("AP",      ev.get("map",  0))), 4),
        "AP50": round(float(ev.get("AP50",     ev.get("ap50", 0))), 4),
        "AP75": round(float(ev.get("AP75",     ev.get("ap75", 0))), 4),
        "AR":   round(float(ev.get("ARmax100", ev.get("ar",   0))), 4),
    }

val_metrics  = extract_coco(val_eval)
test_metrics = extract_coco(test_eval)

# -----------------------------------------------------------------------

print("\n  Exporting models (SavedModel + Float32 TFLite + INT8 TFLite)...")

# 1. SavedModel — original format, equivalent to .h5 in the gesture module.
#    Use this for fine-tuning, ONNX export, or any non-TFLite conversion.
model.export(
    export_dir=str(MODELS_DIR),
    export_format=[ExportFormat.SAVED_MODEL],
)
print(f"  Saved: {SAVED_MODEL_DIR}/")

# 2. Float32 TFLite — no quantization; used as the baseline in
#    compare_raw_vs_tflite.py to measure accuracy loss from INT8 quantization.
model.export(
    export_dir=str(MODELS_DIR),
    tflite_filename="cube_detector_float32.tflite",
)
print(f"  Saved: {FLOAT32_MODEL_PATH}")

# 3. INT8 TFLite — fully quantized; required for Google Coral EdgeTPU.
#    Used below for the P/R/F1 evaluation on the test set.
quant_config = QuantizationConfig.for_int8(representative_data=train_data)
model.export(
    export_dir=str(MODELS_DIR),
    tflite_filename="cube_detector_int8.tflite",
    quantization_config=quant_config,
)
print(f"  Saved: {MODEL_PATH}")

# -----------------------------------------------------------------------

print("\n  Computing Precision / Recall / F1 on test set (TFLite INT8)...")
import tensorflow as tf
input_size = tf.lite.Interpreter(model_path=str(MODEL_PATH)) \
                .get_input_details()[0]['shape'][1]
test_prf = evaluate_detection(test_items, MODEL_PATH, input_size)
p, r, f1, tp, fp, fn = test_prf
print(f"  Precision={p:.4f}  Recall={r:.4f}  F1={f1:.4f}  "
      f"TP={tp}  FP={fp}  FN={fn}")

# -----------------------------------------------------------------------

print("\n  Saving metadata...")
metadata = {
    "model":        "EfficientDet-Lite0",
    "image_size":   args.image_size,
    "classes":      ["cube"],
    "epochs":       args.epochs,
    "batch_size":   args.batch_size,
    "train_images": len(train_items),
    "val_images":   len(val_items),
    "test_images":  len(test_items),
    "val_metrics":  val_metrics,
    "test_metrics": {
        **test_metrics,
        "precision": round(p,  4),
        "recall":    round(r,  4),
        "f1":        round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn,
    },
}
with open(METADATA_PATH, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"  Saved: {METADATA_PATH}")

# -----------------------------------------------------------------------

print("\n[7/7] Generating output files...")
val_m_full = {**val_metrics,
              "epochs": args.epochs, "batch_size": args.batch_size,
              "train_images": len(train_items), "val_images": len(val_items),
              "test_images":  len(test_items),  "image_size": args.image_size}

generate_outputs(val_m_full, test_metrics, test_prf, test_items)

# -----------------------------------------------------------------------

print("\n" + "=" * 60)
print("Training complete!")
print(f"  Model:    {MODEL_PATH}")
print(f"  Metadata: {METADATA_PATH}")
print(f"  Outputs:  {args.output_dir}/")
print()
print(f"  Val  AP50 = {val_metrics['AP50']:.4f}   mAP = {val_metrics['mAP']:.4f}")
print(f"  Test AP50 = {test_metrics['AP50']:.4f}   mAP = {test_metrics['mAP']:.4f}")
print(f"  Test P={p:.4f}  R={r:.4f}  F1={f1:.4f}")
print()
print("Next steps:")
print(f"  edgetpu_compiler -s {MODEL_PATH}")
print(f"  python scripts/test_inference.py")
print("=" * 60)
