from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA_YAML = ROOT / "datasets" / "final" / "data.yaml"

if not DATA_YAML.exists():
    raise FileNotFoundError("Run scripts/prepare_dataset.py first.")

model = YOLO("yolo11n.pt")
model.train(
    data=str(DATA_YAML),
    epochs=30,
    imgsz=416,
    batch=2,
    device="cpu",
    workers=0,
    patience=10,
    project=str(ROOT / "results"),
    name="snail_detection_cpu"
)
print("Training finished. Check results/snail_detection_cpu/weights/best.pt")
