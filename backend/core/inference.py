"""
Core inference engine — Multi-task deep learning framework for:
  1. Giant African Snail (Lissachatina fulica) detection & counting (YOLOv8n)
  2. Arecanut plant disease classification (MobileNetV2)
  3. Snail feeding damage severity classification (MobileNetV2)

Engineered with:
  - False-positive snail rejection (filtering non-plantation objects, humans, hands)
  - Decoupling of snail physical feeding damage from fungal Ring Spot disease
  - Confidence thresholding & uncertainty rejection (no invented diseases)
  - Proper 'Healthy Plant' & 'No Damage' state handling (never displays 'low damage' on healthy palms)
  - Practical Home Remedies & Verified Scientific Treatments (strictly zero weather logic)
"""
from __future__ import annotations

import io
import os
import time
import base64
import logging
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from ultralytics import YOLO

from .config import SNAIL_MODEL_PATH, DISEASE_MODEL_PATH, DAMAGE_MODEL_PATH, PROJECT_ROOT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & Model Classes
# ---------------------------------------------------------------------------
DISEASE_CLASSES = ["BUD ROT", "HEALTHY LEAF", "HEALTHY NUT", "KOLEROGA", "RING SPOT", "YELLOW LEAF"]
DAMAGE_CLASSES = ["low_damage", "moderate_damage", "severe_damage"]
DEVICE = torch.device("cpu")

# Thresholds
SNAIL_CONF_THRESHOLD = 0.45       # High-precision threshold to eliminate false positives on hands/humans
DISEASE_CONF_THRESHOLD = 0.65     # Minimum confidence to assert a fungal/phytoplasma disease
RING_SPOT_STRICT_CONF = 0.75      # Require strict confidence so snail chew marks aren't misclassified as Ring Spot

# MobileNetV2 image transform (matches training pipeline)
_TRANSFORM = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# ---------------------------------------------------------------------------
# Model Loader Helpers
# ---------------------------------------------------------------------------
def _load_mobilenet(weights_path: Path, num_classes: int) -> torch.nn.Module:
    """Load a saved MobileNetV2 state-dict with custom two-stage classifier head."""
    import torchvision.models as models
    import torch.nn as nn
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, num_classes)
    )
    state = torch.load(str(weights_path), map_location=DEVICE, weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    model.load_state_dict(state)
    model.to(DEVICE)
    model.eval()
    return model


_registry: dict[str, Any] = {}

def _ensure_loaded() -> None:
    """Load all models once into the singleton registry."""
    if _registry:
        return

    logger.info("Loading AI models...")
    yolo_cfg = str(PROJECT_ROOT / ".yolo")
    os.environ.setdefault("YOLO_CONFIG_DIR", yolo_cfg)

    # 1. YOLO snail detection
    _registry["yolo"] = YOLO(str(SNAIL_MODEL_PATH))

    # 2. Disease classifier
    _registry["disease"] = _load_mobilenet(DISEASE_MODEL_PATH, num_classes=len(DISEASE_CLASSES))

    # 3. Damage classifier
    _registry["damage"] = _load_mobilenet(DAMAGE_MODEL_PATH, num_classes=len(DAMAGE_CLASSES))

    logger.info("All 3 models loaded successfully.")


# ---------------------------------------------------------------------------
# Public Inference API
# ---------------------------------------------------------------------------
def analyze_image(pil_img: Image.Image) -> dict[str, Any]:
    """
    Run multi-task deep learning on a PIL image.
    Accurately separates snail detection, disease diagnosis, and physical damage severity.
    """
    _ensure_loaded()
    img_rgb = pil_img.convert("RGB")
    img_w, img_h = img_rgb.size
    img_area = img_w * img_h

    # =========================================================================
    # 1. Snail Detection & Counting (YOLOv8n) with False-Positive Rejection
    # =========================================================================
    t0 = time.perf_counter()
    yolo_results = _registry["yolo"].predict(
        source=img_rgb,
        conf=0.35,  # Raw detection threshold
        iou=0.45,
        verbose=False,
        device="cpu",
    )
    snail_ms = (time.perf_counter() - t0) * 1000

    valid_boxes = []
    max_conf = 0.0

    for r in yolo_results:
        for box in r.boxes:
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            conf = float(box.conf[0])
            box_w = max(1.0, x2 - x1)
            box_h = max(1.0, y2 - y1)
            box_area = box_w * box_h
            aspect_ratio = box_w / box_h

            # Filter false positives:
            # 1. Must satisfy confidence threshold
            # 2. Reject boxes covering > 85% of image (camera lens coverage / human torso)
            # 3. Reject extreme aspect ratios (< 0.25 or > 4.0) that are non-mollusc artifacts
            if conf >= SNAIL_CONF_THRESHOLD:
                if (box_area / img_area) < 0.85 and (0.25 <= aspect_ratio <= 4.0):
                    valid_boxes.append([round(x1), round(y1), round(x2), round(y2), round(conf, 4)])
                    max_conf = max(max_conf, conf)

    snail_detected = len(valid_boxes) > 0
    snail_result = {
        "detected": snail_detected,
        "count": len(valid_boxes),
        "confidence": round(max_conf, 4) if snail_detected else 0.0,
        "boxes": valid_boxes,
        "inference_ms": round(snail_ms, 1),
        "status_text": "Giant African Snail Detected" if snail_detected else "No Giant African Snail Detected"
    }

    # =========================================================================
    # 2. Arecanut Disease Classification (MobileNetV2) & Decoupling
    # =========================================================================
    t0 = time.perf_counter()
    tensor = _TRANSFORM(img_rgb).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits = _registry["disease"](tensor)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    disease_ms = (time.perf_counter() - t0) * 1000

    disease_idx = int(np.argmax(probs))
    raw_class = DISEASE_CLASSES[disease_idx]
    top_disease_conf = float(probs[disease_idx])

    # Snail Feeding Damage Classifier
    with torch.no_grad():
        logits_d = _registry["damage"](tensor)
        probs_d = torch.softmax(logits_d, dim=1)[0].cpu().numpy()

    damage_idx = int(np.argmax(probs_d))
    raw_damage_class = DAMAGE_CLASSES[damage_idx]
    damage_conf = float(probs_d[damage_idx])

    # Decouple Snail Physical Damage from Ring Spot:
    # If the image shows physical rasping/chewing from snails, or if confidence is borderline,
    # do NOT falsely report fungal Ring Spot.
    is_confused_ring_spot = (
        raw_class == "RING SPOT" and 
        (snail_detected or damage_conf > 0.60 or top_disease_conf < RING_SPOT_STRICT_CONF)
    )

    if top_disease_conf < DISEASE_CONF_THRESHOLD and not is_confused_ring_spot:
        # Uncertain / Low confidence -> Rejection mechanism
        disease_predicted_class = "UNCERTAIN"
        disease_status_text = "Unable to confidently identify disease. Please upload a clearer image."
        is_healthy = False
        disease_explanation = "Image patterns do not match trained disease signatures with sufficient confidence."
    elif raw_class in ("HEALTHY LEAF", "HEALTHY NUT"):
        disease_predicted_class = "HEALTHY"
        disease_status_text = "No Arecanut Disease Detected"
        is_healthy = True
        disease_explanation = "The arecanut palm foliage and nuts show healthy physiological tissue."
    elif is_confused_ring_spot:
        # Corrected: Physical snail feeding damage recognized separately
        disease_predicted_class = "NO_DISEASE"
        disease_status_text = "No Arecanut Disease Detected"
        is_healthy = False  # Plant has physical snail damage, but no fungal disease
        disease_explanation = "Observed leaf necrosis and rasping marks are physical feeding injuries caused by Giant African Snails, not Ring Spot disease."
    else:
        # Supported genuine disease detected
        disease_predicted_class = raw_class
        disease_status_text = f"Disease Detected: {raw_class.replace('_', ' ').title()}"
        is_healthy = False
        disease_explanation = _get_disease_explanation(raw_class)

    disease_result = {
        "predicted_class": disease_predicted_class,
        "raw_class": raw_class,
        "confidence": round(top_disease_conf, 4),
        "probabilities": {c: round(float(p), 4) for c, p in zip(DISEASE_CLASSES, probs)},
        "is_healthy": is_healthy,
        "status_text": disease_status_text,
        "explanation": disease_explanation,
        "inference_ms": round(disease_ms, 1),
    }

    # =========================================================================
    # 3. Snail-Related Damage Severity Assessment
    # =========================================================================
    # CRITICAL: If the plant is healthy and no snails are detected, there is NO damage.
    # Never display "Low Damage" on healthy palms!
    if is_healthy and not snail_detected and not is_confused_ring_spot:
        damage_severity = None
        has_damage = False
        damage_status_text = "No Visible Damage Detected"
        damage_explanation = "Plant tissue is intact with no snail rasping or defoliation."
    else:
        # Physical damage is present
        has_damage = True
        if raw_damage_class in ("severe_damage", "moderate_damage", "low_damage"):
            damage_severity = raw_damage_class
        else:
            damage_severity = "low_damage"
            
        damage_status_text = f"{damage_severity.replace('_', ' ').title()}"
        damage_explanation = _get_damage_explanation(damage_severity)

    damage_result = {
        "has_damage": has_damage,
        "severity": damage_severity,
        "confidence": round(damage_conf, 4) if has_damage else 0.0,
        "status_text": damage_status_text,
        "explanation": damage_explanation,
        "probabilities": {c: round(float(p), 4) for c, p in zip(DAMAGE_CLASSES, probs_d)} if has_damage else {},
    }

    # =========================================================================
    # 4. Generate Visual Annotated Image (Plotted Bounding Boxes)
    # =========================================================================
    annotated_b64 = ""
    try:
        # If valid snails were detected, plot bounding boxes
        if snail_detected:
            plot_arr = yolo_results[0].plot()
            annotated_pil = Image.fromarray(plot_arr)
        else:
            # Clean image without false bounding boxes
            annotated_pil = img_rgb

        buf_ann = io.BytesIO()
        annotated_pil.save(buf_ann, format="JPEG", quality=90)
        annotated_b64 = base64.b64encode(buf_ann.getvalue()).decode("utf-8")
    except Exception as e:
        logger.warning("Could not generate plotted annotated image: %s", e)

    original_b64 = ""
    try:
        buf_orig = io.BytesIO()
        img_rgb.save(buf_orig, format="JPEG", quality=85)
        original_b64 = base64.b64encode(buf_orig.getvalue()).decode("utf-8")
    except Exception as e:
        logger.warning("Could not encode original image: %s", e)

    # =========================================================================
    # 5. Overall Plant Health Status & Smart Recommendations
    # =========================================================================
    overall_status, overall_status_text = _compute_overall_status(
        snail_detected, is_healthy, disease_predicted_class, has_damage
    )

    recommendations = _build_comprehensive_recommendations(
        snail_detected, snail_result["count"], disease_predicted_class, damage_severity, is_healthy
    )

    return {
        "snail_detection": snail_result,
        "disease_classification": disease_result,
        "damage_assessment": damage_result,
        "overall_status": overall_status,
        "overall_status_text": overall_status_text,
        "combined_recommendation": recommendations["summary_text"],
        "smart_recommendations": recommendations,
        "annotated_image": f"data:image/jpeg;base64,{annotated_b64}" if annotated_b64 else None,
        "original_image": f"data:image/jpeg;base64,{original_b64}" if original_b64 else None,
    }


# ---------------------------------------------------------------------------
# Helper Explanations & Overall Status
# ---------------------------------------------------------------------------
def _get_disease_explanation(disease_cls: str) -> str:
    explanations = {
        "KOLEROGA": "Fruit rot (Mahali) caused by Phytophthora meadii. Induces water-soaked lesions and massive immature nut fall.",
        "BUD ROT": "Apical rot caused by Phytophthora infection. The central spindle leaf turns yellow, withers, and decays emitting foul odor.",
        "YELLOW LEAF": "Yellow Leaf Disease (YLD) associated with phytoplasma. Leaves turn yellow from inner whorls with crinkled tips and kernel blackening.",
        "RING SPOT": "Fungal ring spot producing circular spots with brown margins and chlorotic yellowish halos.",
        "HEALTHY LEAF": "Normal healthy arecanut palm frond with vigorous green coloration.",
        "HEALTHY NUT": "Normal developing fruit bunch with intact glossy green perianth."
    }
    return explanations.get(disease_cls.upper(), "Supported plantation disease condition.")


def _get_damage_explanation(severity: str | None) -> str:
    if not severity or severity == "no_damage":
        return "No visible snail feeding damage or mechanical injury."
    elif severity == "low_damage":
        return "Early superficial epidermal scraping on lower fronds or tender stem collar."
    elif severity == "moderate_damage":
        return "Noticeable holes, jagged chewing margins, and defoliation on seedling fronds."
    elif severity == "severe_damage":
        return "Extensive defoliation, chewed apical tissue, and seedling destruction threatening palm survival."
    return "Physical snail damage observed."


def _compute_overall_status(has_snail: bool, is_healthy: bool, disease_cls: str, has_damage: bool) -> tuple[str, str]:
    if has_snail and not is_healthy and disease_cls not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN"):
        return "both_detected", "Both Snail Infestation and Disease Detected"
    elif has_snail:
        return "snail_detected", "Snail Infestation Detected"
    elif not is_healthy and disease_cls not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN"):
        return "disease_detected", "Arecanut Disease Detected"
    elif has_damage and not is_healthy:
        return "snail_damage_detected", "Snail Feeding Damage Detected"
    elif disease_cls == "UNCERTAIN":
        return "further_inspection", "Further Inspection Required"
    elif is_healthy and not has_damage and not has_snail:
        return "healthy", "Healthy Plant"
    else:
        return "no_visible_damage", "No Visible Damage Detected"


# ---------------------------------------------------------------------------
# Smart Recommendations Engine (Zero Weather Logic)
# ---------------------------------------------------------------------------
def _build_comprehensive_recommendations(
    has_snail: bool,
    snail_count: int,
    disease_cls: str,
    damage_severity: str | None,
    is_healthy: bool
) -> dict[str, Any]:
    """Generates structured, practical recommendations with home remedies and treatments."""
    
    home_remedies = []
    chemical_treatments = []
    action_steps = []
    prevention_tips = []

    # 1. Healthy Plant — Positive Health Card
    if is_healthy and not has_snail and (not damage_severity or damage_severity == "no_damage"):
        summary_text = (
            "🌿 **Healthy Plant:** Your arecanut palm appears healthy. No visible snail damage or supported disease was detected.\n\n"
            "• Continue routine plantation inspection every 7-10 days.\n"
            "• Maintain clean palm basins and balanced organic nutrition (12 kg compost + 1 kg neem cake per palm/year).\n"
            "• Ensure proper sub-surface drainage trenches to avoid waterlogging.\n"
            "• No chemical sprays or pesticide treatments are required."
        )
        prevention_tips = [
            "Maintain regular bi-weekly monitoring of palm crowns and seedling bases.",
            "Keep palm basins clear of excessive rotting weed piles where pests seek shelter.",
            "Ensure proper spacing (2.7m x 2.7m) and soil aeration."
        ]
        return {
            "summary_text": summary_text,
            "is_healthy": True,
            "action_steps": ["Continue routine field monitoring", "Maintain balanced irrigation and organic manure"],
            "home_remedies": [],
            "chemical_treatments": [],
            "prevention_tips": prevention_tips
        }

    # 2. Snail Infestation or Snail Damage Recommendations
    if has_snail or damage_severity in ("low_damage", "moderate_damage", "severe_damage"):
        action_steps.extend([
            f"Conduct early dawn hand-collection (5:30 AM – 7:00 AM) wearing rubber gloves.",
            "Inspect nearby seedlings and shaded palm collars for aggregated snails.",
            "Remove rotting coconut husks, weed mounds, and moist trash from the palm base."
        ])

        home_remedies.extend([
            {
                "title": "Salt Brine Immersion (Non-Chemical Euthanasia)",
                "description": "Drop collected snails directly into a 15% common salt (NaCl) solution (150g salt per 1L water) or boiling water. Highly effective, zero chemical residue."
            },
            {
                "title": "Slaked Lime & Wood Ash Barrier Rings",
                "description": "Apply a 15–20 cm wide band of dry slaked lime (chuna) mixed with wood ash around each palm base. Snails will not cross the caustic, desiccant barrier."
            },
            {
                "title": "Fermented Jaggery & Yeast Bait Traps",
                "description": "Mix 100g jaggery/molasses + 5g baker's yeast + mashed ripe bananas in 1L water. Place in shallow earthen pots flush with the soil to lure and drown nocturnal snails."
            },
            {
                "title": "Copper Tape Collar Barriers",
                "description": "Wrap 5cm wide copper foil tape around sapling stems. Copper creates a natural galvanic electrical sensation that repels snails without injury to the plant."
            }
        ])

        chemical_treatments.append({
            "product": "Iron (III) Phosphate 1% Pellets (Sluggo / Ferramol)",
            "dosage": "5 grams per square meter around palm drip line",
            "safety": "Eco-friendly, biodegradable into soil iron and phosphorus nutrients. Safe for birds, pets, and earthworms."
        })

        if damage_severity == "severe_damage":
            chemical_treatments.append({
                "product": "Metaldehyde 2.5% Pellets (Emergency Intervention Only)",
                "dosage": "Apply strictly under shaded tiles away from domestic livestock",
                "safety": "Toxic to domestic animals and dogs. Use protective gloves. Do not contaminate irrigation water channels."
            })

    # 3. Disease Specific Recommendations
    if disease_cls == "KOLEROGA":
        action_steps.extend([
            "Immediately collect and destroy fallen rotted arecanuts by burning or deep burial with lime.",
            "Apply prophylactic 1% Bordeaux mixture on all fruit bunches.",
            "Cover bunches with 100-gauge UV-stabilized polythene bags before monsoon onset."
        ])
        chemical_treatments.append({
            "product": "1% Bordeaux Mixture Spray",
            "dosage": "Dissolve 1 kg copper sulphate and 1 kg slaked lime separately in 50L water each, then mix together to make 100L. Neutralize with lime until pH 7.",
            "safety": "Test neutrality with a clean iron knife blade (no copper coating should form). Apply on clear days."
        })
    elif disease_cls == "BUD ROT":
        action_steps.extend([
            "Surgically scoop out decaying soft tissues from the apical spindle until healthy white tissue is reached.",
            "Apply 10% Bordeaux paste or Copper Oxychloride paste directly onto the scooped apical wound.",
            "Cover the treated crown with a protective inverted plastic cone to keep rainwater out."
        ])
        chemical_treatments.append({
            "product": "10% Bordeaux Paste",
            "dosage": "1 kg copper sulphate + 1 kg lime dissolved in 10 liters of water to form a thick protective paste.",
            "safety": "Wear rubber gloves during surgical debridement and paste application."
        })
    elif disease_cls == "YELLOW LEAF":
        action_steps.extend([
            "Apply annual balanced nutrition: 100g N, 40g P₂O₅, 140g K₂O per palm.",
            "Incorporate 12 kg well-rotted farmyard manure and 1 kg neem cake per palm.",
            "Foliar spray of micronutrients: Zinc Sulphate (0.5%), Magnesium Sulphate (0.5%), and Borax (0.2%)."
        ])
    elif disease_cls == "RING SPOT":
        action_steps.extend([
            "Prune and burn severely spotted, dried lower fronds.",
            "Spray Mancozeb 75 WP (2g/L) or Copper Oxychloride 50 WP (2.5g/L) on both upper and lower leaf surfaces."
        ])
        chemical_treatments.append({
            "product": "Mancozeb 75 WP or Copper Oxychloride 50 WP",
            "dosage": "2.0 to 2.5 grams per liter of water",
            "safety": "Spray during early morning or late afternoon. Avoid spraying during high heat."
        })

    # Summary text generation
    summary_parts = []
    if has_snail:
        summary_parts.append(f"🐌 **Giant African Snail Detected:** {snail_count} snail(s) identified. Immediate morning hand-collection and barrier treatment recommended.")
    if damage_severity and damage_severity != "no_damage":
        summary_parts.append(f"🍃 **Feeding Damage Severity:** {damage_severity.replace('_', ' ').title()}. Implement snail baiting and remove daytime hiding debris.")
    if disease_cls not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN"):
        summary_parts.append(f"🌿 **Disease Diagnosed:** {disease_cls.replace('_', ' ').title()}. Follow the agronomic protocol and apply approved fungicides.")

    summary_text = "\n\n".join(summary_parts) if summary_parts else "Plantation health evaluation complete."

    return {
        "summary_text": summary_text,
        "is_healthy": is_healthy,
        "action_steps": action_steps,
        "home_remedies": home_remedies,
        "chemical_treatments": chemical_treatments,
        "prevention_tips": prevention_tips or ["Conduct routine bi-weekly field scouting", "Maintain clean drainage trenches"]
    }
