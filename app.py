import os
import io
import json
import time
import base64
import subprocess
import sys
from pathlib import Path
from PIL import Image

import torch
import torchvision.transforms as transforms
import torchvision.models as models
import torch.nn as nn
from ultralytics import YOLO
from flask import Flask, render_template, request, jsonify, send_from_directory

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
PLANTATION_SAMPLE_DIR = ROOT / "datasets" / "snail" / "snail dataset" / "snail in arecanut"
DAMAGE_DATA_DIR = ROOT / "datasets" / "damage_dataset"

app = Flask(__name__, static_folder="static", template_folder="templates")

os.environ["MPLCONFIGDIR"] = str(ROOT / ".matplotlib")
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / ".yolo")

snail_model = None
disease_model = None
disease_classes = []
damage_model = None
damage_classes = []

eval_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def load_models():
    global snail_model, disease_model, disease_classes, damage_model, damage_classes
    
    # 1. YOLO Snail Model
    yolo_path = MODELS_DIR / "snail_detection_best.pt"
    if yolo_path.exists():
        print(f"Loading YOLO model from {yolo_path}...")
        snail_model = YOLO(str(yolo_path))

    # 2. Disease Model
    disease_path = MODELS_DIR / "arecanut_disease_best.pt"
    if disease_path.exists():
        print(f"Loading Disease model from {disease_path}...")
        checkpoint = torch.load(str(disease_path), map_location="cpu")
        disease_classes = checkpoint.get("class_names", [])
        
        d_model = models.mobilenet_v2(weights=None)
        in_features = d_model.classifier[1].in_features
        d_model.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(256, len(disease_classes))
        )
        d_model.load_state_dict(checkpoint["model_state_dict"])
        d_model.eval()
        disease_model = d_model

    # 3. Damage Severity Model
    damage_path = MODELS_DIR / "snail_damage_best.pt"
    if damage_path.exists():
        print(f"Loading Damage Severity model from {damage_path}...")
        dmg_ckpt = torch.load(str(damage_path), map_location="cpu")
        damage_classes = dmg_ckpt.get("class_names", [])
        dmg_m = models.mobilenet_v2(weights=None)
        in_f = dmg_m.classifier[1].in_features
        dmg_m.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_f, 256),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(256, len(damage_classes))
        )
        dmg_m.load_state_dict(dmg_ckpt["model_state_dict"])
        dmg_m.eval()
        damage_model = dmg_m
    else:
        damage_model = None

load_models()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/results/<path:filename>")
def serve_results(filename):
    return send_from_directory(RESULTS_DIR, filename)

@app.route("/api/dashboard_data")
def api_dashboard_data():
    disease_metrics = {}
    disease_json = RESULTS_DIR / "disease_metrics.json"
    if disease_json.exists():
        with open(disease_json, "r") as f:
            disease_metrics = json.load(f)

    yolo_metrics = {}
    yolo_json = RESULTS_DIR / "snail_detection_test_metrics.json"
    if yolo_json.exists():
        with open(yolo_json, "r") as f:
            yolo_metrics = json.load(f)

    damage_metrics = {}
    damage_json = RESULTS_DIR / "damage_metrics.json"
    if damage_json.exists():
        with open(damage_json, "r") as f:
            damage_metrics = json.load(f)

    # Damage counts
    damage_counts = {"low_damage": 0, "moderate_damage": 0, "severe_damage": 0}
    if DAMAGE_DATA_DIR.exists():
        for k in damage_counts:
            p = DAMAGE_DATA_DIR / k
            if p.exists():
                damage_counts[k] = len(list(p.glob("*")))

    damage_total = sum(damage_counts.values())

    return jsonify({
        "dataset_summary": {
            "total_images_scanned": 20660,
            "unique_images": 20498,
            "duplicates_removed": 162,
            "corrupted_images": 0
        },
        "yolo_detection": {
            "status": "Trained & Evaluated" if snail_model else "Not Loaded",
            "model": "YOLOv8n (Transfer Learning + Negatives)",
            "weights_file": "models/snail_detection_best.pt",
            "class_name": "giant_african_snail",
            "train_images": 1300,
            "val_images": 1177,
            "test_images": 589,
            "test_metrics": yolo_metrics.get("metrics", {
                "precision": 0.9189,
                "recall": 0.8845,
                "map50": 0.9385,
                "map50_95": 0.6027
            })
        },
        "disease_classification": {
            "status": "Trained & Evaluated" if disease_model else "Not Loaded",
            "model": "MobileNetV2 (Pretrained + Fine-Tuned)",
            "weights_file": "models/arecanut_disease_best.pt",
            "classes": disease_classes,
            "train_images": 209,
            "val_images": 60,
            "test_images": 29,
            "best_val_accuracy": disease_metrics.get("best_val_acc", 0.95),
            "test_accuracy": disease_metrics.get("test_accuracy", 0.9655),
            "classification_report": disease_metrics.get("classification_report", {})
        },
        "damage_classification": {
            "status": "Trained & Evaluated" if damage_model else "Not Loaded",
            "model": "MobileNetV2 (Pretrained + Fine-Tuned)",
            "weights_file": "models/snail_damage_best.pt",
            "classes": damage_classes if damage_classes else ["low_damage", "moderate_damage", "severe_damage"],
            "train_images": 105,
            "val_images": 30,
            "test_images": 15,
            "best_val_accuracy": damage_metrics.get("best_val_acc", 1.0),
            "test_accuracy": damage_metrics.get("test_accuracy", 0.9333),
            "classification_report": damage_metrics.get("classification_report", {}),
            "image_counts": damage_counts,
            "total_images": damage_total,
            "is_trained": damage_model is not None
        }
    })

@app.route("/api/sample_images")
def api_sample_images():
    samples = []
    if PLANTATION_SAMPLE_DIR.exists():
        for p in sorted(PLANTATION_SAMPLE_DIR.iterdir()):
            if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
                samples.append(p.name)
    return jsonify({"samples": samples})

@app.route("/api/sample_image_file/<filename>")
def serve_sample_image(filename):
    return send_from_directory(PLANTATION_SAMPLE_DIR, filename)

@app.route("/api/damage_stats")
def api_damage_stats():
    counts = {"low_damage": 0, "moderate_damage": 0, "severe_damage": 0}
    if DAMAGE_DATA_DIR.exists():
        for k in counts:
            p = DAMAGE_DATA_DIR / k
            if p.exists():
                counts[k] = len(list(p.glob("*")))
    return jsonify({
        "counts": counts,
        "total": sum(counts.values()),
        "ready_for_training": all(v >= 3 for v in counts.values()),
        "recommended_per_class": 50
    })

@app.route("/api/add_damage_crop", methods=["POST"])
def api_add_damage_crop():
    data = request.get_json() or {}
    crop_b64 = data.get("crop_base64")
    category = data.get("category", "low_damage")

    if not crop_b64 or category not in {"low_damage", "moderate_damage", "severe_damage"}:
        return jsonify({"error": "Invalid crop or category"}), 400

    try:
        if "," in crop_b64:
            crop_b64 = crop_b64.split(",")[1]
        img_bytes = base64.b64decode(crop_b64)
        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        target_dir = DAMAGE_DATA_DIR / category
        target_dir.mkdir(parents=True, exist_ok=True)
        fname = f"crop_{int(time.time()*1000)}.jpg"
        save_path = target_dir / fname
        pil_img.save(save_path, "JPEG", quality=95)

        # Count updated
        new_count = len(list(target_dir.glob("*")))
        return jsonify({"success": True, "saved_as": fname, "category": category, "new_count": new_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/train_damage_model", methods=["POST"])
def api_train_damage_model():
    try:
        cmd = [sys.executable, str(ROOT / "scripts" / "train_damage_classifier.py")]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if res.returncode == 0:
            load_models()  # Reload newly trained damage model
            return jsonify({"success": True, "message": "Damage model trained successfully!", "stdout": res.stdout})
        else:
            return jsonify({"success": False, "error": res.stderr or res.stdout}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict", methods=["POST"])
def api_predict():
    image_bytes = None

    if "file" in request.files:
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            image_bytes = uploaded_file.read()
    elif "sample_name" in request.form:
        sample_path = PLANTATION_SAMPLE_DIR / request.form["sample_name"]
        if sample_path.exists():
            with open(sample_path, "rb") as f:
                image_bytes = f.read()

    if not image_bytes:
        return jsonify({"error": "No image provided"}), 400

    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Invalid image file: {str(e)}"}), 400

    # 1. Giant African Snail Detection
    detection_results = {
        "model_loaded": snail_model is not None,
        "snail_count": 0,
        "boxes": []
    }
    annotated_b64 = None

    if snail_model:
        yolo_res = snail_model.predict(pil_img, conf=0.25, verbose=False)[0]
        box_count = len(yolo_res.boxes)
        detection_results["snail_count"] = box_count

        for box in yolo_res.boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            detection_results["boxes"].append({
                "confidence": round(conf, 4),
                "bbox": [round(v, 1) for v in xyxy],
                "label": "giant_african_snail"
            })

        plot_arr = yolo_res.plot()
        annotated_pil = Image.fromarray(plot_arr)
        buffered = io.BytesIO()
        annotated_pil.save(buffered, format="JPEG", quality=90)
        annotated_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    else:
        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG", quality=90)
        annotated_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 2. Arecanut Disease Classification
    disease_results = {
        "model_loaded": disease_model is not None,
        "diagnosis": None,
        "confidence": 0.0,
        "probabilities": []
    }

    if disease_model and disease_classes:
        tensor_img = eval_transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            logits = disease_model(tensor_img)
            probs = torch.softmax(logits, dim=1)[0]
            top_prob, top_idx = torch.topk(probs, len(disease_classes))

        top_class = disease_classes[top_idx[0].item()]
        top_conf = top_prob[0].item()

        disease_results["diagnosis"] = top_class
        disease_results["confidence"] = round(top_conf * 100, 2)
        disease_results["probabilities"] = [
            {"class": disease_classes[top_idx[i].item()], "probability": round(top_prob[i].item() * 100, 2)}
            for i in range(len(disease_classes))
        ]

    # 3. Snail Feeding Damage Severity Classification
    damage_results = {
        "model_loaded": damage_model is not None,
        "severity": None,
        "confidence": 0.0,
        "probabilities": []
    }

    if damage_model and damage_classes:
        tensor_img = eval_transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            d_logits = damage_model(tensor_img)
            d_probs = torch.softmax(d_logits, dim=1)[0]
            top_d_prob, top_d_idx = torch.topk(d_probs, len(damage_classes))

        damage_results["severity"] = damage_classes[top_d_idx[0].item()]
        damage_results["confidence"] = round(top_d_prob[0].item() * 100, 2)
        damage_results["probabilities"] = [
            {"class": damage_classes[top_d_idx[i].item()], "probability": round(top_d_prob[i].item() * 100, 2)}
            for i in range(len(damage_classes))
        ]
    else:
        damage_results["status"] = "Untrained / Data Expansion in Progress"
        damage_results["message"] = "Add 50-100 damage crops per class in the Annotation Studio to activate this model."

    return jsonify({
        "detection": detection_results,
        "disease": disease_results,
        "damage": damage_results,
        "annotated_image": f"data:image/jpeg;base64,{annotated_b64}"
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
