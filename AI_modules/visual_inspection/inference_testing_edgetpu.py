"""
Visual Inspection Inference on Google Coral EdgeTPU
Model: inspection_model_int8_edgetpu_src_edgetpu.tflite (uint8 I/O)
Supports webcam and dataset evaluation with binary-specific quality metrics.

Dataset mode:
    python inference_testing_edgetpu.py --mode dataset --dataset dataset/split/test \
        --output results/edgetpu_results.json --charts results/edgetpu_charts/

Webcam mode:
    python inference_testing_edgetpu.py --mode webcam
"""

import time
import os
import argparse
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
import seaborn as sns
from pycoral.utils.edgetpu import make_interpreter
from pycoral.adapters import common
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_auc_score,
    roc_curve,
)

IMAGE_SIZE = (224, 224)
FAIL_IDX = 0   # class_names index for FAIL (positive / defect class)


class InspectionEdgeTPUInference:
    def __init__(self, model_path, metadata_path=None):
        print("Initializing EdgeTPU interpreter...")
        self.interpreter = make_interpreter(model_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Read quantization params for output dequantization
        self.out_scale, self.out_zp = self.output_details[0]["quantization"]
        self.input_size = common.input_size(self.interpreter)  # (W, H)

        self.labels = ["FAIL", "PASS"]
        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path) as f:
                self.labels = json.load(f).get("class_names", self.labels)
        print(f"Input size: {self.input_size}  Classes: {self.labels}")
        print("EdgeTPU ready.")

    def preprocess(self, frame):
        img = cv2.resize(frame, self.input_size)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img.astype(np.uint8)

    def infer(self, frame):
        inp = self.preprocess(frame)
        common.set_input(self.interpreter, inp)

        t0 = time.perf_counter()
        self.interpreter.invoke()
        latency = (time.perf_counter() - t0) * 1000

        # Dequantize uint8 output → float32 probabilities
        raw_out = self.interpreter.get_tensor(self.output_details[0]["index"])[0]
        probs = (raw_out.astype(np.float32) - self.out_zp) * self.out_scale
        # Clamp to [0, 1] (quantization rounding can slightly exceed bounds)
        probs = np.clip(probs, 0.0, 1.0)

        class_id = int(np.argmax(probs))
        return {
            "class_id": class_id,
            "label": self.labels[class_id],
            "confidence": float(probs[class_id]),
            "probs": probs.tolist(),
            "latency_ms": latency,
        }


def run_webcam_demo(model_path, metadata_path=None, camera_id=0, threshold=0.7):
    inferencer = InspectionEdgeTPUInference(model_path, metadata_path)
    cap = cv2.VideoCapture(camera_id)
    assert cap.isOpened(), f"Cannot open camera {camera_id}"
    print("Starting real-time inspection (press 'q' to quit)...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        result = inferencer.infer(frame)
        color = (0, 200, 0) if result["label"] == "PASS" else (0, 0, 220)
        text = f"{result['label']} ({result['confidence']*100:.1f}%) | {result['latency_ms']:.1f} ms"
        cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        if result["label"] == "FAIL" and result["confidence"] >= threshold:
            cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 220), 4)
        cv2.imshow("Visual Inspection - EdgeTPU", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def run_dataset_inference(model_path, metadata_path, dataset_path, output_file=None, charts_dir=None):
    inferencer = InspectionEdgeTPUInference(model_path, metadata_path)
    labels = inferencer.labels
    fail_label = labels[FAIL_IDX]

    results = []
    y_true, y_pred = [], []
    y_score_fail = []
    class_accuracy = {}
    total_latency = 0
    image_count = 0

    class_dirs = sorted([d for d in os.listdir(dataset_path)
                         if os.path.isdir(os.path.join(dataset_path, d))])
    print(f"Running EdgeTPU inference on dataset: {dataset_path}")
    print("=" * 60)

    for class_name in class_dirs:
        class_path = os.path.join(dataset_path, class_name)
        image_files = sorted([f for f in os.listdir(class_path)
                              if f.lower().endswith((".jpg", ".jpeg", ".png"))])
        print(f"\nClass: {class_name} ({len(image_files)} images)")
        correct = 0

        for img_file in image_files:
            frame = cv2.imread(os.path.join(class_path, img_file))
            if frame is None:
                print(f"  ! Skipped {img_file} (cannot read)")
                continue

            result = inferencer.infer(frame)
            ground_truth = class_name.upper()
            predicted = result["label"].upper()
            result["ground_truth"] = ground_truth
            result["correct"] = predicted == ground_truth
            result["image_path"] = os.path.join(class_path, img_file)

            if result["correct"]:
                correct += 1

            results.append(result)
            y_true.append(ground_truth)
            y_pred.append(predicted)
            y_score_fail.append(result["probs"][FAIL_IDX])
            total_latency += result["latency_ms"]
            image_count += 1

            status = "+" if result["correct"] else "x"
            print(f"  [{status}] {img_file}: {result['label']} ({result['confidence']*100:.1f}%) {result['latency_ms']:.1f}ms")

        if image_files:
            acc = correct / len(image_files) * 100
            class_accuracy[class_name.upper()] = acc
            print(f"  Class Accuracy: {acc:.1f}% ({correct}/{len(image_files)})")

    print("\n" + "=" * 60)
    print("INFERENCE SUMMARY")
    print("=" * 60)

    if image_count == 0:
        print("No images processed.")
        return results

    correct_total = sum(1 for r in results if r["correct"])
    avg_latency = total_latency / image_count
    overall_accuracy = correct_total / image_count * 100

    y_true_bin = [1 if t == fail_label else 0 for t in y_true]
    y_pred_bin = [1 if p == fail_label else 0 for p in y_pred]

    cm = confusion_matrix(y_true_bin, y_pred_bin)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        fnr = fn / (fn + tp) * 100 if (fn + tp) > 0 else 0.0
        fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0.0
    else:
        fnr = fpr = 0.0

    auc = roc_auc_score(y_true_bin, y_score_fail) if len(set(y_true_bin)) > 1 else float("nan")

    print(f"Total images:      {image_count}")
    print(f"Overall Accuracy:  {overall_accuracy:.2f}% ({correct_total}/{image_count})")
    print(f"Average Latency:   {avg_latency:.2f} ms")
    print(f"ROC AUC:           {auc:.4f}")
    print(f"False Neg Rate:    {fnr:.2f}%  (missed defects)")
    print(f"False Pos Rate:    {fpr:.2f}%  (good parts rejected)")

    if output_file:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        serializable = []
        for r in results:
            rc = {k: (int(v) if isinstance(v, np.integer) else
                      float(v) if isinstance(v, np.floating) else v)
                  for k, v in r.items()}
            serializable.append(rc)
        with open(output_file, "w") as f:
            json.dump(serializable, f, indent=2)
        print(f"\nResults saved to: {output_file}")

    if charts_dir:
        os.makedirs(charts_dir, exist_ok=True)
        unique_classes = sorted(set(y_true))

        # 1. Confusion matrix
        cm_lbl = confusion_matrix(y_true, y_pred, labels=unique_classes)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm_lbl, annot=True, fmt="d", cmap="Blues",
                    xticklabels=unique_classes, yticklabels=unique_classes,
                    cbar_kws={"label": "Count"})
        plt.title("Confusion Matrix - EdgeTPU", fontsize=13, fontweight="bold")
        plt.ylabel("Ground Truth")
        plt.xlabel("Predicted")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "confusion_matrix.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: confusion_matrix.png")

        # 2. Per-class accuracy
        classes = sorted(class_accuracy.keys())
        accs = [class_accuracy[c] for c in classes]
        bar_colors = ["#d32f2f" if c == "FAIL" else "#388e3c" for c in classes]
        plt.figure(figsize=(6, 5))
        bars = plt.bar(classes, accs, color=bar_colors, edgecolor="black", linewidth=1.2)
        plt.axhline(overall_accuracy, color="navy", linestyle="--", label=f"Overall: {overall_accuracy:.1f}%")
        for bar in bars:
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f"{bar.get_height():.1f}%", ha="center", va="bottom", fontweight="bold")
        plt.ylim(0, 108)
        plt.ylabel("Accuracy (%)")
        plt.title("Per-Class Accuracy - EdgeTPU", fontsize=13, fontweight="bold")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "per_class_accuracy.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: per_class_accuracy.png")

        # 3. Confidence score histogram
        scores_true_fail = [y_score_fail[i] for i in range(len(y_true)) if y_true[i] == fail_label]
        scores_true_pass = [y_score_fail[i] for i in range(len(y_true)) if y_true[i] != fail_label]
        plt.figure(figsize=(8, 5))
        plt.hist(scores_true_fail, bins=30, alpha=0.65, color="#d32f2f", label="True FAIL", density=True)
        plt.hist(scores_true_pass, bins=30, alpha=0.65, color="#388e3c", label="True PASS", density=True)
        plt.axvline(0.5, color="black", linestyle="--", label="Default threshold (0.5)")
        plt.xlabel("FAIL-class Confidence Score")
        plt.ylabel("Density")
        plt.title("FAIL Score Distribution by Ground Truth - EdgeTPU", fontweight="bold")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "confidence_histogram.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: confidence_histogram.png")

        # 4. ROC curve
        if not np.isnan(auc):
            fpr_curve, tpr_curve, _ = roc_curve(y_true_bin, y_score_fail)
            plt.figure(figsize=(6, 6))
            plt.plot(fpr_curve, tpr_curve, color="#1565c0", lw=2, label=f"ROC AUC = {auc:.4f}")
            plt.plot([0, 1], [0, 1], "k--", lw=1)
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate (Recall)")
            plt.title("ROC Curve - EdgeTPU", fontweight="bold")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "roc_curve.png"), dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Saved: roc_curve.png")

        # 5. Threshold sweep
        thresholds = np.linspace(0.05, 0.95, 37)
        fnr_list, fpr_list, acc_list = [], [], []
        y_true_arr = np.array(y_true_bin)
        y_score_arr = np.array(y_score_fail)
        for t in thresholds:
            y_pred_t = (y_score_arr >= t).astype(int)
            cm_t = confusion_matrix(y_true_arr, y_pred_t, labels=[0, 1])
            if cm_t.shape == (2, 2):
                tn_t, fp_t, fn_t, tp_t = cm_t.ravel()
                fnr_list.append(fn_t / (fn_t + tp_t) * 100 if (fn_t + tp_t) > 0 else 0.0)
                fpr_list.append(fp_t / (fp_t + tn_t) * 100 if (fp_t + tn_t) > 0 else 0.0)
                acc_list.append((tp_t + tn_t) / len(y_true_arr) * 100)
            else:
                fnr_list.append(0); fpr_list.append(0); acc_list.append(0)

        fig, ax1 = plt.subplots(figsize=(9, 5))
        ax1.plot(thresholds, fnr_list, color="#d32f2f", lw=2, label="FNR (missed defects)")
        ax1.plot(thresholds, fpr_list, color="#f57c00", lw=2, label="FPR (false rejections)")
        ax1.set_xlabel("FAIL Confidence Threshold")
        ax1.set_ylabel("Rate (%)")
        ax1.set_ylim(0, 105)
        ax2 = ax1.twinx()
        ax2.plot(thresholds, acc_list, color="#1565c0", lw=2, linestyle="--", label="Accuracy")
        ax2.set_ylabel("Accuracy (%)", color="#1565c0")
        ax2.set_ylim(0, 105)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right")
        ax1.axvline(0.5, color="gray", linestyle=":", lw=1.2)
        plt.title("Threshold Analysis - EdgeTPU", fontweight="bold")
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, "threshold_analysis.png"), dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: threshold_analysis.png")

        # 6. Classification report
        report = classification_report(y_true, y_pred, target_names=unique_classes, digits=4)
        report_path = os.path.join(charts_dir, "classification_report.txt")
        with open(report_path, "w") as f:
            f.write("CLASSIFICATION REPORT - EDGETPU MODEL\n")
            f.write("=" * 60 + "\n")
            f.write(f"Overall Accuracy: {overall_accuracy:.2f}% ({correct_total}/{image_count})\n")
            f.write(f"Average Latency:  {avg_latency:.2f} ms\n")
            f.write(f"ROC AUC:          {auc:.4f}\n")
            f.write(f"False Neg Rate:   {fnr:.2f}%  (missed defects)\n")
            f.write(f"False Pos Rate:   {fpr:.2f}%  (good parts rejected)\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)
        print(f"Saved: classification_report.txt")

        # 7. Summary
        summary_path = os.path.join(charts_dir, "inference_summary.txt")
        with open(summary_path, "w") as f:
            f.write("INFERENCE SUMMARY - EDGETPU MODEL\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total images:      {image_count}\n")
            f.write(f"Overall Accuracy:  {overall_accuracy:.2f}% ({correct_total}/{image_count})\n")
            f.write(f"Average Latency:   {avg_latency:.2f} ms\n")
            f.write(f"Total Time:        {total_latency/1000:.2f} s\n")
            f.write(f"ROC AUC:           {auc:.4f}\n")
            f.write(f"False Neg Rate:    {fnr:.2f}%  (missed defects — lower is better)\n")
            f.write(f"False Pos Rate:    {fpr:.2f}%  (good parts rejected)\n\n")
            f.write("Per-Class Accuracy:\n")
            for cls in sorted(class_accuracy):
                f.write(f"  {cls}: {class_accuracy[cls]:.2f}%\n")
        print(f"Saved: inference_summary.txt")
        print(f"\nAll charts saved to: {charts_dir}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visual Inspection - EdgeTPU Evaluation")
    parser.add_argument("--model",
                        default="models/inspection_model_int8_edgetpu_src_edgetpu.tflite",
                        help="EdgeTPU compiled .tflite model path")
    parser.add_argument("--metadata", default="models/model_metadata.json")
    parser.add_argument("--mode", choices=["webcam", "dataset"], default="webcam")
    parser.add_argument("--dataset", help="Dataset folder (class sub-dirs: PASS/, FAIL/)")
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=0.7, help="FAIL alert threshold (webcam)")
    parser.add_argument("--output", help="Output JSON file (dataset mode)")
    parser.add_argument("--charts", help="Directory for chart outputs (dataset mode)")
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"ERROR: Model not found: {args.model}")
        exit(1)

    if args.mode == "webcam":
        run_webcam_demo(args.model, args.metadata, args.camera_id, args.threshold)
    else:
        if not args.dataset or not os.path.isdir(args.dataset):
            print("ERROR: --dataset <path> required for dataset mode")
            exit(1)
        if not args.charts and args.output:
            args.charts = os.path.join(os.path.dirname(args.output) or ".", "charts")
        print("=" * 60)
        print("MODE: Dataset Evaluation (EdgeTPU)")
        print("=" * 60)
        run_dataset_inference(args.model, args.metadata, args.dataset, args.output, args.charts)
