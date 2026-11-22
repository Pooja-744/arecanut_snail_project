import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHTS = ROOT / "models" / "snail_detection_best.pt"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "predictions"

parser = argparse.ArgumentParser(description="Detect and count Giant African Snails in arecanut plantation images.")
parser.add_argument("--source", required=True, help="Path to an image or directory")
parser.add_argument("--weights", default=str(DEFAULT_WEIGHTS), help="Path to trained YOLO weights")
parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
parser.add_argument("--project", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for annotated images")
parser.add_argument("--name", default="cli_predict", help="Subfolder name for predictions")
args = parser.parse_args()

if not Path(args.weights).exists():
    raise FileNotFoundError(f"Weights file not found at: {args.weights}")

print(f"Loading Giant African Snail detection model from: {args.weights}")
model = YOLO(args.weights)

results = model.predict(
    source=args.source,
    conf=args.conf,
    save=True,
    project=args.project,
    name=args.name,
    exist_ok=True
)

for i, result in enumerate(results, start=1):
    count = len(result.boxes) if result.boxes is not None else 0
    img_name = Path(result.path).name if hasattr(result, "path") else f"Image {i}"
    print(f"\n[{img_name}] Detected {count} Giant African Snail(s)")
    if count > 0:
        for b_idx, box in enumerate(result.boxes, 1):
            conf = float(box.conf[0])
            xyxy = [round(v, 1) for v in box.xyxy[0].tolist()]
            print(f"  - Snail #{b_idx}: Confidence = {conf*100:.1f}%, BBox = {xyxy}")

print(f"\nAnnotated predictions saved to: {Path(args.project) / args.name}")
