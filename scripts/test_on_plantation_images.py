import os
from pathlib import Path
from PIL import Image
import torch
import torchvision.transforms as transforms
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
YOLO_MODEL_PATH = ROOT / "models" / "snail_detection_best.pt"
DISEASE_MODEL_PATH = ROOT / "models" / "arecanut_disease_best.pt"
PLANTATION_SNAIL_DIR = ROOT / "datasets" / "snail" / "snail dataset" / "snail in arecanut"
OUTPUT_DIR = ROOT / "results" / "plantation_test_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load YOLO model
print(f"Loading YOLO Model from {YOLO_MODEL_PATH}...")
yolo_model = YOLO(str(YOLO_MODEL_PATH))

# 2. Load Disease Model
print(f"Loading Disease Model from {DISEASE_MODEL_PATH}...")
checkpoint = torch.load(str(DISEASE_MODEL_PATH), map_location="cpu")
class_names = checkpoint["class_names"]

import torchvision.models as models
import torch.nn as nn
disease_model = models.mobilenet_v2(weights=None)
in_features = disease_model.classifier[1].in_features
disease_model.classifier = nn.Sequential(
    nn.Dropout(p=0.3),
    nn.Linear(in_features, 256),
    nn.ReLU(),
    nn.Dropout(p=0.2),
    nn.Linear(256, len(class_names))
)
disease_model.load_state_dict(checkpoint["model_state_dict"])
disease_model.eval()

eval_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

print("\n" + "=" * 70)
print("TESTING TRAINED MODELS ON REAL ARECANUT PLANTATION IMAGES (17 IMAGES)")
print("=" * 70)

images = [p for p in PLANTATION_SNAIL_DIR.iterdir() if p.suffix.lower() in {'.jpg', '.png', '.webp', '.jpeg'}]
print(f"Found {len(images)} plantation images in {PLANTATION_SNAIL_DIR.name}")

results_summary = []

for i, img_path in enumerate(sorted(images), 1):
    print(f"\n--- Image {i}/{len(images)}: {img_path.name} ---")

    # Run YOLO snail detection
    res = yolo_model.predict(str(img_path), conf=0.25, save=True, project=str(OUTPUT_DIR), name="predictions", exist_ok=True)[0]
    box_count = len(res.boxes)
    confidences = [float(b.conf[0]) for b in res.boxes] if box_count > 0 else []

    print(f"  [Snail Detection] Detected Snails: {box_count}")
    if box_count > 0:
        for idx, c in enumerate(confidences):
            print(f"    - Snail #{idx+1} Confidence: {c*100:.1f}%")
    else:
        print("    - No snail detected at confidence threshold >= 0.25")

    # Run Disease / Plant Condition classification
    try:
        pil_img = Image.open(img_path).convert("RGB")
        tensor_img = eval_transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            logits = disease_model(tensor_img)
            probs = torch.softmax(logits, dim=1)[0]
            top_prob, top_idx = torch.topk(probs, 3)

        top_class = class_names[top_idx[0].item()]
        top_conf = top_prob[0].item()
        print(f"  [Plant Condition] Diagnosis: {top_class} ({top_conf*100:.1f}%)")
        print(f"    Top 3 probabilities:")
        for k in range(3):
            c_name = class_names[top_idx[k].item()]
            prob_k = top_prob[k].item()
            print(f"      {k+1}. {c_name}: {prob_k*100:.1f}%")
    except Exception as e:
        print(f"  [Plant Condition] Error analyzing: {e}")

    results_summary.append({
        "image": img_path.name,
        "snails_detected": box_count,
        "confidences": confidences,
        "top_plant_condition": top_class,
        "plant_condition_confidence": float(top_conf)
    })

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
total_detected = sum(r["snails_detected"] for r in results_summary)
images_with_snails = sum(1 for r in results_summary if r["snails_detected"] > 0)
print(f"Total plantation images tested: {len(images)}")
print(f"Images with positive snail detections: {images_with_snails}/{len(images)} ({images_with_snails/len(images)*100:.1f}%)")
print(f"Total individual snail instances detected: {total_detected}")
print(f"Annotated test predictions saved to: {OUTPUT_DIR / 'predictions'}")
