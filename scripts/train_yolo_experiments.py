import os
import json
import shutil
from pathlib import Path
import pandas as pd
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA_YAML = ROOT / "datasets" / "snail_yolo" / "data.yaml"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results" / "yolo"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_experiments():
    print("=" * 70)
    print("ULTRALYTICS YOLO GIANT AFRICAN SNAIL DETECTION TRAINING")
    print("=" * 70)
    
    experiments = [
        {
            "name": "exp1_yolov8n_baseline",
            "model_weights": "yolov8n.pt",
            "epochs": 5,
            "imgsz": 416,
            "batch": 8,
            "lr0": 0.01,
            "patience": 3,
            "mosaic": 1.0,
            "mixup": 0.0
        },
        {
            "name": "exp2_yolo11n_optimized",
            "model_weights": "yolo11n.pt",
            "epochs": 5,
            "imgsz": 416,
            "batch": 8,
            "lr0": 0.005,
            "patience": 3,
            "mosaic": 0.5,
            "mixup": 0.1
        }
    ]

    exp_summaries = []
    best_overall_map50 = -1.0
    best_exp_name = None
    best_weights_source = None

    for exp in experiments:
        exp_name = exp["name"]
        print(f"\n>>> Starting Experiment: {exp_name}")
        print(f"    Architecture: {exp['model_weights']}")
        print(f"    Epochs: {exp['epochs']}, Batch: {exp['batch']}, ImgSz: {exp['imgsz']}, LR: {exp['lr0']}")

        model = YOLO(exp["model_weights"])
        results = model.train(
            data=str(DATA_YAML),
            epochs=exp["epochs"],
            imgsz=exp["imgsz"],
            batch=exp["batch"],
            lr0=exp["lr0"],
            mosaic=exp["mosaic"],
            mixup=exp["mixup"],
            patience=exp["patience"],
            device="cpu",
            workers=0,
            project=str(RESULTS_DIR),
            name=exp_name,
            exist_ok=True,
            verbose=True
        )

        exp_dir = RESULTS_DIR / exp_name
        exp_best_weights = exp_dir / "weights" / "best.pt"

        # Validate on full test split
        print(f"\nEvaluating {exp_name} on UNSEEN TEST SPLIT (589 images)...")
        eval_model = YOLO(str(exp_best_weights))
        test_metrics = eval_model.val(data=str(DATA_YAML), split="test", imgsz=exp["imgsz"], device="cpu", workers=0)

        # Extract real metrics
        prec = float(test_metrics.box.mp)
        rec = float(test_metrics.box.mr)
        map50 = float(test_metrics.box.map50)
        map50_95 = float(test_metrics.box.map)

        print(f"--- {exp_name} Test Set Evaluation Results ---")
        print(f"  Precision: {prec:.4f} ({prec*100:.2f}%)")
        print(f"  Recall:    {rec:.4f} ({rec*100:.2f}%)")
        print(f"  mAP@50:    {map50:.4f} ({map50*100:.2f}%)")
        print(f"  mAP@50-95: {map50_95:.4f} ({map50_95*100:.2f}%)")

        summary = {
            "experiment": exp_name,
            "weights": exp["model_weights"],
            "hyperparameters": exp,
            "test_precision": prec,
            "test_recall": rec,
            "test_map50": map50,
            "test_map50_95": map50_95,
            "exp_dir": str(exp_dir)
        }
        exp_summaries.append(summary)

        if map50 > best_overall_map50:
            best_overall_map50 = map50
            best_exp_name = exp_name
            best_weights_source = exp_best_weights

    # Save overall best model to models/
    final_best_dest = MODELS_DIR / "snail_detection_best.pt"
    if best_weights_source and best_weights_source.exists():
        shutil.copy2(best_weights_source, final_best_dest)
        print(f"\n[+] Champion model selected: {best_exp_name} (mAP@50: {best_overall_map50*100:.2f}%)")
        print(f"    Saved champion weights to: {final_best_dest}")

    # Copy key plots to results root for easy viewing
    best_exp_dir = RESULTS_DIR / best_exp_name
    for plot_file in ["results.png", "confusion_matrix.png", "BoxPR_curve.png", "PR_curve.png", "F1_curve.png"]:
        src_plot = best_exp_dir / plot_file
        if src_plot.exists():
            shutil.copy2(src_plot, ROOT / "results" / f"snail_yolo_{plot_file}")

    # Save full comparison JSON
    comparison_data = {
        "experiments": exp_summaries,
        "champion_experiment": best_exp_name,
        "champion_weights": str(final_best_dest.relative_to(ROOT)),
        "champion_test_metrics": {
            "precision": next(e["test_precision"] for e in exp_summaries if e["experiment"] == best_exp_name),
            "recall": next(e["test_recall"] for e in exp_summaries if e["experiment"] == best_exp_name),
            "map50": next(e["test_map50"] for e in exp_summaries if e["experiment"] == best_exp_name),
            "map50_95": next(e["test_map50_95"] for e in exp_summaries if e["experiment"] == best_exp_name)
        }
    }
    with open(ROOT / "results" / "snail_yolo_experiments.json", "w") as f:
        json.dump(comparison_data, f, indent=2)

    print("\nYOLO Experiments Completed Successfully!")

if __name__ == "__main__":
    run_experiments()
