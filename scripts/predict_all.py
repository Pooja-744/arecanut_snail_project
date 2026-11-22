import argparse
from pathlib import Path
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_YOLO_WEIGHTS = ROOT / "models" / "snail_detection_best.pt"
DEFAULT_DISEASE_WEIGHTS = ROOT / "models" / "arecanut_disease_best.pt"
DEFAULT_DAMAGE_WEIGHTS = ROOT / "models" / "snail_damage_best.pt"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "predictions"

parser = argparse.ArgumentParser(description="Multi-Task Snail Detection, Disease Diagnosis, and Feeding Damage Severity Inference.")
parser.add_argument("--image", required=True, help="Path to input image")
parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
args = parser.parse_args()

img_path = Path(args.image)
if not img_path.exists():
    raise FileNotFoundError(f"Image not found: {img_path}")

print("=" * 65)
print(f"MULTI-TASK PLANTATION HEALTH ANALYSIS: {img_path.name}")
print("=" * 65)

# Standard evaluation transform
tfm = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
pil_img = Image.open(img_path).convert("RGB")
tensor_img = tfm(pil_img).unsqueeze(0)

# 1. Giant African Snail Detection
if DEFAULT_YOLO_WEIGHTS.exists():
    yolo_model = YOLO(str(DEFAULT_YOLO_WEIGHTS))
    res = yolo_model.predict(
        str(img_path),
        conf=args.conf,
        save=True,
        project=str(DEFAULT_OUTPUT_DIR),
        name="joint_cli",
        exist_ok=True,
        verbose=False
    )[0]
    box_count = len(res.boxes)
    print(f"\n[1] GIANT AFRICAN SNAIL DETECTION:")
    print(f"    Total Snails Detected: {box_count}")
    for idx, box in enumerate(res.boxes, 1):
        c = float(box.conf[0])
        print(f"    - Snail #{idx}: Confidence = {c*100:.1f}%, BBox = {[round(v,1) for v in box.xyxy[0].tolist()]}")
    print(f"    Annotated output saved to: {DEFAULT_OUTPUT_DIR / 'joint_cli' / img_path.name}")
else:
    print("\n[1] YOLO model weights not found.")

# 2. Arecanut Disease Classification
if DEFAULT_DISEASE_WEIGHTS.exists():
    ckpt = torch.load(str(DEFAULT_DISEASE_WEIGHTS), map_location="cpu")
    class_names = ckpt["class_names"]
    
    d_model = models.mobilenet_v2(weights=None)
    in_features = d_model.classifier[1].in_features
    d_model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, len(class_names))
    )
    d_model.load_state_dict(ckpt["model_state_dict"])
    d_model.eval()

    with torch.no_grad():
        logits = d_model(tensor_img)
        probs = torch.softmax(logits, dim=1)[0]
        top_prob, top_idx = torch.topk(probs, 3)

    print(f"\n[2] ARECANUT PLANTATION HEALTH DIAGNOSIS:")
    print(f"    Top Diagnosis: {class_names[top_idx[0].item()]} ({top_prob[0].item()*100:.1f}%)")
    print(f"    Probabilities:")
    for k in range(min(3, len(class_names))):
        c_name = class_names[top_idx[k].item()]
        p_val = top_prob[k].item()
        print(f"      {k+1}. {c_name}: {p_val*100:.1f}%")
else:
    print("\n[2] Disease classification weights not found.")

# 3. Snail Feeding Damage Severity Classification
if DEFAULT_DAMAGE_WEIGHTS.exists():
    dmg_ckpt = torch.load(str(DEFAULT_DAMAGE_WEIGHTS), map_location="cpu")
    dmg_classes = dmg_ckpt["class_names"]

    dmg_model = models.mobilenet_v2(weights=None)
    in_f = dmg_model.classifier[1].in_features
    dmg_model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_f, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, len(dmg_classes))
    )
    dmg_model.load_state_dict(dmg_ckpt["model_state_dict"])
    dmg_model.eval()

    with torch.no_grad():
        dmg_logits = dmg_model(tensor_img)
        dmg_probs = torch.softmax(dmg_logits, dim=1)[0]
        top_dmg_prob, top_dmg_idx = torch.topk(dmg_probs, len(dmg_classes))

    print(f"\n[3] SNAIL FEEDING DAMAGE SEVERITY:")
    print(f"    Severity Grade: {dmg_classes[top_dmg_idx[0].item()].replace('_', ' ').upper()} ({top_dmg_prob[0].item()*100:.1f}%)")
    print(f"    Probabilities:")
    for k in range(len(dmg_classes)):
        c_name = dmg_classes[top_dmg_idx[k].item()]
        p_val = top_dmg_prob[k].item()
        print(f"      - {c_name}: {p_val*100:.1f}%")
else:
    print("\n[3] Snail damage model weights not found.")

print("=" * 65)
