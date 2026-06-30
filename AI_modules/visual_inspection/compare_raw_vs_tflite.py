"""
Compare accuracy between:
  - Raw Keras FP32 model (best_model.h5)
  - TFLite INT8 model (inspection_model_int8.tflite, float32 I/O)

Reports overall accuracy, binary quality metrics (FNR, FPR, ROC AUC),
and quantization accuracy drop.

Usage:
    python compare_raw_vs_tflite.py \
        --raw-model models/best_model.h5 \
        --tflite-model models/inspection_model_int8.tflite \
        --dataset dataset/split/test \
        --output results/compare_results.json
"""

import os
import json
import argparse
import numpy as np
import cv2
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
)

IMAGE_SIZE = (224, 224)
FAIL_IDX = 0   # index of FAIL class in class_names


def load_test_dataset(dataset_path):
    images, labels = [], []
    class_names = sorted([d for d in os.listdir(dataset_path)
                          if os.path.isdir(os.path.join(dataset_path, d))])
    class_to_idx = {c: i for i, c in enumerate(class_names)}

    for cls in class_names:
        cls_dir = os.path.join(dataset_path, cls)
        for f in sorted(os.listdir(cls_dir)):
            if not f.lower().endswith((".jpg", ".png", ".jpeg")):
                continue
            img = cv2.imread(os.path.join(cls_dir, f))
            if img is None:
                continue
            img = cv2.resize(img, IMAGE_SIZE)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            images.append(img)
            labels.append(class_to_idx[cls])

    return np.array(images), np.array(labels), class_names


def predict_raw(model, images, batch_size=32):
    preds, scores = [], []
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size].astype(np.float32) / 255.0
        probs = model(batch, training=False).numpy()
        preds.extend(np.argmax(probs, axis=1))
        scores.extend(probs[:, FAIL_IDX].tolist())   # FAIL-class probability
    return np.array(preds), np.array(scores)


def predict_tflite(interpreter, images):
    """CPU TFLite INT8 with float32 I/O — no dequantization needed."""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    preds, scores = [], []
    total = len(images)

    for idx, img in enumerate(images):
        if (idx + 1) % 100 == 0:
            print(f"  TFLite: {idx + 1}/{total}")

        inp = img.astype(np.float32) / 255.0
        inp = np.expand_dims(inp, axis=0)

        interpreter.set_tensor(input_details[0]["index"], inp)
        interpreter.invoke()

        probs = interpreter.get_tensor(output_details[0]["index"])[0]

        # Dequantize if output is still uint8 (should be float32 for CPU model,
        # but guard against an edge case)
        if output_details[0]["dtype"] == np.uint8:
            scale, zp = output_details[0]["quantization"]
            probs = (probs.astype(np.float32) - zp) * scale

        preds.append(int(np.argmax(probs)))
        scores.append(float(probs[FAIL_IDX]))

    return np.array(preds), np.array(scores)


def binary_metrics(labels, preds, scores, class_names):
    """Compute FNR, FPR, AUC for FAIL as the positive class."""
    y_bin = (labels == FAIL_IDX).astype(int)
    p_bin = (preds == FAIL_IDX).astype(int)

    cm = confusion_matrix(y_bin, p_bin)
    fnr = fpr = 0.0
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        fnr = fn / (fn + tp) * 100 if (fn + tp) > 0 else 0.0
        fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0.0

    auc = roc_auc_score(y_bin, scores) if len(set(y_bin)) > 1 else float("nan")
    return fnr, fpr, auc


def main():
    parser = argparse.ArgumentParser(description="Compare Keras FP32 vs TFLite INT8 for visual inspection")
    parser.add_argument("--raw-model", default="models/best_model.h5",
                        help="Keras .h5 FP32 model path")
    parser.add_argument("--tflite-model", default="models/inspection_model_int8.tflite",
                        help="TFLite INT8 model path (float32 I/O)")
    parser.add_argument("--dataset", default="dataset/split/test",
                        help="Test dataset path with class sub-dirs (PASS/, FAIL/)")
    parser.add_argument("--output", default="results/compare_results.json")
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Limit sample count (for quick testing)")
    args = parser.parse_args()

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print("Loading dataset...")
    images, labels, class_names = load_test_dataset(args.dataset)
    if args.max_samples and args.max_samples < len(images):
        images = images[:args.max_samples]
        labels = labels[:args.max_samples]
    print(f"Loaded {len(images)} images  |  Classes: {class_names}")

    print("\nLoading Keras FP32 model...")
    raw_model = tf.keras.models.load_model(args.raw_model)

    print("Loading TFLite INT8 model...")
    interpreter = tf.lite.Interpreter(model_path=args.tflite_model)
    interpreter.allocate_tensors()

    print("\nRunning Keras FP32 inference...")
    preds_raw, scores_raw = predict_raw(raw_model, images)

    print("Running TFLite INT8 inference...")
    preds_tflite, scores_tflite = predict_tflite(interpreter, images)

    acc_raw = accuracy_score(labels, preds_raw)
    acc_tflite = accuracy_score(labels, preds_tflite)
    mismatch = int(np.sum(preds_raw != preds_tflite))

    fnr_raw, fpr_raw, auc_raw = binary_metrics(labels, preds_raw, scores_raw, class_names)
    fnr_tflite, fpr_tflite, auc_tflite = binary_metrics(labels, preds_tflite, scores_tflite, class_names)

    print("\n" + "=" * 60)
    print("ACCURACY COMPARISON")
    print("=" * 60)
    print(f"Keras FP32 Accuracy:    {acc_raw*100:.2f}%")
    print(f"TFLite INT8 Accuracy:   {acc_tflite*100:.2f}%")
    print(f"Accuracy drop:          {(acc_raw - acc_tflite)*100:.2f}%")
    print(f"Prediction mismatch:    {mismatch}/{len(labels)} samples")
    print()
    print(f"{'':20s}  {'FP32':>10s}  {'INT8':>10s}")
    print(f"{'False Neg Rate':20s}  {fnr_raw:9.2f}%  {fnr_tflite:9.2f}%  (missed defects)")
    print(f"{'False Pos Rate':20s}  {fpr_raw:9.2f}%  {fpr_tflite:9.2f}%  (false rejections)")
    print(f"{'ROC AUC':20s}  {auc_raw:10.4f}  {auc_tflite:10.4f}")
    print("=" * 60)

    print("\nKeras FP32 Classification Report:")
    print(classification_report(labels, preds_raw, target_names=class_names, digits=4))

    print("TFLite INT8 Classification Report:")
    print(classification_report(labels, preds_tflite, target_names=class_names, digits=4))

    results = {
        "num_samples": int(len(labels)),
        "class_names": class_names,
        "raw_fp32": {
            "accuracy": float(acc_raw),
            "false_neg_rate_pct": float(fnr_raw),
            "false_pos_rate_pct": float(fpr_raw),
            "roc_auc": float(auc_raw) if not np.isnan(auc_raw) else None,
            "confusion_matrix": confusion_matrix(labels, preds_raw).tolist(),
        },
        "tflite_int8": {
            "accuracy": float(acc_tflite),
            "false_neg_rate_pct": float(fnr_tflite),
            "false_pos_rate_pct": float(fpr_tflite),
            "roc_auc": float(auc_tflite) if not np.isnan(auc_tflite) else None,
            "confusion_matrix": confusion_matrix(labels, preds_tflite).tolist(),
        },
        "quantization_drop": {
            "accuracy_pct": float((acc_raw - acc_tflite) * 100),
            "prediction_mismatch": mismatch,
        },
    }

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
