import json
import shutil
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA_YAML = ROOT / "datasets" / "snail_yolo" / "data.yaml"
EXP1_WEIGHTS = ROOT / "results" / "yolo" / "exp1_yolov8n_baseline" / "weights" / "best.pt"
EVAL_DIR = ROOT / "results" / "yolo" / "eval"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

print(f"Evaluating {EXP1_WEIGHTS} on TEST SPLIT...")
model = YOLO(str(EXP1_WEIGHTS))
metrics = model.val(
    data=str(DATA_YAML),
    split="test",
    imgsz=416,
    device="cpu",
    workers=0,
    project=str(EVAL_DIR),
    name="exp1_test_evaluation",
    exist_ok=True
)

prec = float(metrics.box.mp)
rec = float(metrics.box.mr)
map50 = float(metrics.box.map50)
map50_95 = float(metrics.box.map)

print("\n" + "=" * 60)
print("TEST SPLIT EVALUATION METRICS (589 Unseen Test Images):")
print(f"  Precision: {prec:.4f} ({prec*100:.2f}%)")
print(f"  Recall:    {rec:.4f} ({rec*100:.2f}%)")
print(f"  mAP@50:    {map50:.4f} ({map50*100:.2f}%)")
print(f"  mAP@50-95: {map50_95:.4f} ({map50_95*100:.2f}%)")
print("=" * 60)

test_eval_results = {
    "model": "YOLOv8n Baseline (Transfer Learning)",
    "weights": str(EXP1_WEIGHTS.relative_to(ROOT)),
    "split": "test",
    "test_images_count": 589,
    "metrics": {
        "precision": prec,
        "recall": rec,
        "map50": map50,
        "map50_95": map50_95
    }
}

with open(ROOT / "results" / "snail_detection_test_metrics.json", "w") as f:
    json.dump(test_eval_results, f, indent=2)

# Copy best weights to models/
shutil.copy2(EXP1_WEIGHTS, ROOT / "models" / "snail_detection_best.pt")
print(f"Copied best model to models/snail_detection_best.pt")
