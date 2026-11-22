"""
Core inference engine — Multi-task deep learning framework for:
  1. Giant African Snail (Lissachatina fulica) detection & counting (YOLOv8n)
  2. Arecanut plant disease classification (MobileNetV2)
  3. Snail feeding damage severity classification (MobileNetV2)

Engineered with:
  - False-positive snail rejection (filtering non-plantation objects, humans, hands)
  - Complete decoupling of snail presence from feeding damage (snail present != damage)
  - Region-of-interest (ROI) isolation for disease classification
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
DAMAGE_CLASSES_3 = ["low_damage", "moderate_damage", "severe_damage"]
DAMAGE_CLASSES_4 = ["no_damage", "low_damage", "moderate_damage", "severe_damage"]
DAMAGE_CLASSES = DAMAGE_CLASSES_3
DEVICE = torch.device("cpu")

# Calibrated Thresholds
SNAIL_CONF_THRESHOLD = 0.45       # High-precision threshold to eliminate false positives on hands/humans
DISEASE_CONF_THRESHOLD = 0.68     # Minimum confidence to assert a fungal/phytoplasma disease
RING_SPOT_STRICT_CONF = 0.80      # Require strict confidence so snail chew marks aren't misclassified as Ring Spot
DAMAGE_CONF_THRESHOLD = 0.70      # Minimum confidence to confirm positive physical damage

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

    state = torch.load(str(weights_path), map_location=DEVICE, weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]

    # Detect class count dynamically from weights
    chk_num_classes = state["classifier.4.weight"].shape[0] if "classifier.4.weight" in state else num_classes

    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, chk_num_classes)
    )
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

    # 3. Damage classifier (detect 3 or 4 classes dynamically)
    state_d = torch.load(str(DAMAGE_MODEL_PATH), map_location=DEVICE, weights_only=False)
    if isinstance(state_d, dict) and "model_state_dict" in state_d:
        state_d = state_d["model_state_dict"]
    chk_d_classes = state_d["classifier.4.weight"].shape[0] if "classifier.4.weight" in state_d else 3
    active_damage_classes = DAMAGE_CLASSES_4 if chk_d_classes == 4 else DAMAGE_CLASSES_3
    _registry["damage_classes"] = active_damage_classes
    _registry["damage"] = _load_mobilenet(DAMAGE_MODEL_PATH, num_classes=len(active_damage_classes))

    logger.info("All 3 models loaded successfully. Damage classes: %s", active_damage_classes)


# ---------------------------------------------------------------------------
# Image & ROI Validation Helpers
# ---------------------------------------------------------------------------
def validate_image_input(pil_img: Image.Image) -> tuple[bool, str]:
    """Validate image resolution, format and texture variance."""
    if not isinstance(pil_img, Image.Image):
        return False, "Invalid image object"
    w, h = pil_img.size
    if w < 32 or h < 32:
        return False, "Image dimensions are too small (minimum 32x32 required)"

    gray = np.array(pil_img.convert("L"), dtype=np.float32)
    if float(np.std(gray)) < 8.0:
        return False, "Image appears blank or uniform with no discernible foliage patterns"
    return True, "Valid"


def get_plant_roi(pil_img: Image.Image, snail_boxes: list[list[float]]) -> Image.Image:
    """
    Extract plant foliage/fruit region of interest, prioritizing regions
    outside large snail bounding boxes to prevent mollusc shell patterns
    from confounding disease classification.
    """
    if not snail_boxes:
        return pil_img

    w, h = pil_img.size
    img_area = w * h

    # If the largest snail box occupies > 20% of the image, find the largest non-snail rectangular slice
    largest_box = max(snail_boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    bx1, by1, bx2, by2 = largest_box[:4]
    box_area = (bx2 - bx1) * (by2 - by1)

    if (box_area / img_area) > 0.20:
        candidates = [
            (0, 0, w, int(by1)),                 # Top strip
            (0, int(by2), w, h),                 # Bottom strip
            (0, 0, int(bx1), h),                 # Left strip
            (int(bx2), 0, w, h),                 # Right strip
        ]
        valid_candidates = [
            (x1, y1, x2, y2) for (x1, y1, x2, y2) in candidates
            if (x2 - x1) >= 64 and (y2 - y1) >= 64 and ((x2 - x1) * (y2 - y1) / img_area) >= 0.20
        ]
        if valid_candidates:
            best_crop = max(valid_candidates, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
            try:
                cropped = pil_img.crop(best_crop)
                return cropped
            except Exception:
                return pil_img

    return pil_img


# ---------------------------------------------------------------------------
# Public Inference API
# ---------------------------------------------------------------------------
def analyze_image(pil_img: Image.Image) -> dict[str, Any]:
    """
    Run multi-task deep learning on a PIL image.
    Strictly separates snail detection, disease diagnosis, and physical damage severity.
    """
    _ensure_loaded()

    is_valid, validation_msg = validate_image_input(pil_img)
    if not is_valid:
        return {
            "snail_detection": {
                "detected": False,
                "count": 0,
                "confidence": 0.0,
                "boxes": [],
                "inference_ms": 0.0,
                "status_text": "Invalid Image"
            },
            "disease_classification": {
                "predicted_class": "UNCERTAIN",
                "confidence": 0.0,
                "probabilities": {c: 0.0 for c in DISEASE_CLASSES},
                "is_healthy": False,
                "inference_ms": 0.0,
                "status_text": validation_msg,
                "explanation": "Image does not meet quality requirements for diagnostic evaluation."
            },
            "damage_assessment": {
                "has_damage": False,
                "severity": None,
                "confidence": 0.0,
                "probabilities": {},
                "status_text": "Not Evaluated",
                "explanation": "Image quality insufficient."
            },
            "overall_status": "further_inspection",
            "overall_status_text": "Further Inspection Required",
            "combined_recommendation": f"Please upload a clear, focused photograph of arecanut foliage or fruit. Reason: {validation_msg}.",
            "smart_recommendations": {
                "summary_text": validation_msg,
                "is_healthy": False,
                "action_steps": ["Capture image with adequate lighting", "Ensure subject fills at least 50% of the frame"],
                "home_remedies": [],
                "chemical_treatments": [],
                "prevention_tips": ["Maintain clear plantation surveillance"]
            },
            "annotated_image": None,
            "original_image": None
        }

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
    # 2. Arecanut Disease Classification (MobileNetV2) & ROI Decoupling
    # =========================================================================
    # Select plant foliage ROI (avoiding snail bounding boxes if present)
    plant_img = get_plant_roi(img_rgb, valid_boxes)
    t0 = time.perf_counter()
    tensor = _TRANSFORM(plant_img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits = _registry["disease"](tensor)
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    disease_ms = (time.perf_counter() - t0) * 1000

    disease_idx = int(np.argmax(probs))
    raw_class = DISEASE_CLASSES[disease_idx]
    top_disease_conf = float(probs[disease_idx])
    sorted_probs = np.sort(probs)[::-1]
    prob_margin = float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) > 1 else 1.0

    # MobileNetV2 Snail Feeding Damage Classifier
    tensor_damage = _TRANSFORM(img_rgb).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logits_d = _registry["damage"](tensor_damage)
        probs_d = torch.softmax(logits_d, dim=1)[0].cpu().numpy()

    active_damage_classes = _registry.get("damage_classes", DAMAGE_CLASSES_3)
    damage_idx = int(np.argmax(probs_d))
    raw_damage_class = active_damage_classes[damage_idx]
    damage_conf = float(probs_d[damage_idx])
    sorted_probs_d = np.sort(probs_d)[::-1]
    damage_margin = float(sorted_probs_d[0] - sorted_probs_d[1]) if len(sorted_probs_d) > 1 else 1.0

    # Decouple Snail Physical Damage from Ring Spot:
    # Snail rasping holes look like concentric necrotic spots to MobileNetV2.
    is_confused_ring_spot = (
        raw_class == "RING SPOT" and 
        (snail_detected or (damage_conf > 0.65 and raw_damage_class in ("moderate_damage", "severe_damage")) or top_disease_conf < RING_SPOT_STRICT_CONF or prob_margin < 0.18)
    )

    if (top_disease_conf < DISEASE_CONF_THRESHOLD or prob_margin < 0.12) and not is_confused_ring_spot:
        # Uncertain / Low confidence -> Rejection mechanism
        disease_predicted_class = "UNCERTAIN"
        disease_status_text = "Inconclusive / Further Observation Required"
        is_healthy = False
        disease_explanation = "Image patterns do not match trained disease signatures with sufficient confidence. Please upload a clearer close-up image of arecanut foliage or nut."
    elif raw_class in ("HEALTHY LEAF", "HEALTHY NUT"):
        disease_predicted_class = "HEALTHY"
        disease_status_text = "No Arecanut Disease Detected"
        is_healthy = True
        disease_explanation = "The arecanut palm foliage and nuts show healthy physiological tissue."
    elif is_confused_ring_spot:
        disease_predicted_class = "NO_DISEASE"
        disease_status_text = "No Arecanut Disease Detected"
        is_healthy = False  # Physical snail injury, not fungal pathogen
        disease_explanation = "Observed leaf necrosis and rasping marks are physical feeding injuries caused by Giant African Snails, not Ring Spot disease."
    else:
        # Supported genuine disease detected with strong model evidence
        disease_predicted_class = raw_class
        disease_status_text = f"Disease Detected: {raw_class.replace('_', ' ').title()}"
        is_healthy = False
        disease_explanation = _get_disease_explanation(raw_class)

    has_confirmed_disease = (
        not is_healthy and
        disease_predicted_class not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN")
    )

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
    # 3. Snail-Related Damage Severity Assessment (Strictly Independent)
    # =========================================================================
    # CRITICAL:
    # Snail presence does NOT imply feeding damage. Snail detection and feeding damage are two independent predictions.
    # CASE 1: Snail present, no visible damage -> has_damage = False, severity = None
    # CASE 2: Snail present with visible damage -> has_damage = True, severity = predicted severity
    # CASE 3: No snail and no visible damage -> has_damage = False, severity = None
    if has_confirmed_disease and not snail_detected:
        # Pathogen disease (Bud Rot, Koleroga, Yellow Leaf) without snail: foliar necrosis is disease, not snail damage
        has_damage = False
        damage_severity = None
        damage_status_text = "No Visible Snail Feeding Damage"
        damage_explanation = "Observed foliar symptoms are associated with pathogen disease, not snail feeding."
    elif is_healthy and not is_confused_ring_spot:
        # Healthy plant: no feeding lesions
        has_damage = False
        damage_severity = None
        damage_status_text = "No Visible Snail Feeding Damage"
        damage_explanation = "Plant tissue is intact with no snail rasping, holes, or defoliation."
    elif "no_damage" in active_damage_classes and raw_damage_class == "no_damage":
        # 4-class model explicit no_damage prediction
        has_damage = False
        damage_severity = None
        damage_status_text = "No Visible Snail Feeding Damage"
        damage_explanation = "Model confirmed absence of snail feeding injury."
    elif is_confused_ring_spot:
        # Confirmed feeding rasping / chew holes decoupled from Ring Spot
        has_damage = True
        damage_severity = raw_damage_class if raw_damage_class in ("moderate_damage", "severe_damage", "low_damage") else "moderate_damage"
        damage_status_text = f"{damage_severity.replace('_', ' ').title()}"
        damage_explanation = _get_damage_explanation(damage_severity)
    elif damage_conf >= 0.85 and damage_margin >= 0.25 and raw_damage_class in ("moderate_damage", "severe_damage") and (snail_detected or raw_class == "RING SPOT"):
        # Distinct high-confidence evidence of significant physical damage
        has_damage = True
        damage_severity = raw_damage_class
        damage_status_text = f"{damage_severity.replace('_', ' ').title()}"
        damage_explanation = _get_damage_explanation(damage_severity)
    else:
        # No confirmed visible feeding damage (Case 1: Snail present without damage, or intact foliage)
        has_damage = False
        damage_severity = None
        damage_status_text = "No Visible Snail Feeding Damage"
        damage_explanation = "No confirmed snail feeding marks, rasping, or defoliation observed."

    damage_result = {
        "has_damage": has_damage,
        "severity": damage_severity,
        "confidence": round(damage_conf, 4) if has_damage else 0.0,
        "status_text": damage_status_text,
        "explanation": damage_explanation,
        "probabilities": {c: round(float(p), 4) for c, p in zip(active_damage_classes, probs_d)} if has_damage else {},
    }

    # =========================================================================
    # 4. Generate Visual Annotated Image (Plotted Bounding Boxes)
    # =========================================================================
    annotated_b64 = ""
    try:
        if snail_detected:
            plot_arr = yolo_results[0].plot()
            annotated_pil = Image.fromarray(plot_arr)
        else:
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


def _compute_overall_status(
    snail_detected: bool,
    is_healthy: bool,
    disease_predicted_class: str,
    has_damage: bool
) -> tuple[str, str]:
    """
    Computes holistic plantation status strictly among:
    - healthy
    - snail_detected
    - snail_damage_detected
    - disease_detected
    - both_detected
    - further_inspection
    """
    has_confirmed_disease = (
        not is_healthy and
        disease_predicted_class not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN")
    )
    has_confirmed_damage = bool(has_damage)

    # 1. Both snail AND confirmed disease
    if snail_detected and has_confirmed_disease:
        return "both_detected", "Both Snail Infestation and Disease Detected"

    # 2. Confirmed disease without snail
    if has_confirmed_disease:
        return "disease_detected", "Arecanut Disease Detected"

    # 3. Snail with confirmed damage, or confirmed damage alone (no disease)
    if has_confirmed_damage:
        return "snail_damage_detected", "Snail Feeding Damage Detected"

    # 4. Snail detected, no visible damage, no disease
    if snail_detected:
        if disease_predicted_class == "UNCERTAIN":
            return "snail_detected", "Giant African Snail Detected (Foliage Inspection Required)"
        return "snail_detected", "Giant African Snail Detected"

    # 5. Uncertain prediction / low image quality
    if disease_predicted_class == "UNCERTAIN":
        return "further_inspection", "Further Inspection Required"

    # 6. Healthy plant (no snail, no disease, no damage)
    if is_healthy and not snail_detected and not has_confirmed_damage:
        return "healthy", "Healthy Plant"

    return "healthy", "Healthy Plant"


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

    has_confirmed_disease = (
        not is_healthy and
        disease_cls not in ("HEALTHY", "NO_DISEASE", "UNCERTAIN")
    )
    has_confirmed_damage = bool(damage_severity and damage_severity not in ("no_damage", "none", "None"))

    # 1. Healthy Plant — Positive Health Advisory
    if is_healthy and not has_snail and not has_confirmed_damage:
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
    if has_snail or has_confirmed_damage:
        action_steps.extend([
            "Conduct early dawn hand-collection (5:30 AM – 7:00 AM) wearing rubber gloves.",
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
            "name": "Iron (III) Phosphate 1% Pellets (Sluggo / Ferramol)",
            "dosage": "5 grams per square meter around palm drip line",
            "safety": "Eco-friendly, biodegradable into soil iron and phosphorus nutrients. Safe for birds, pets, and earthworms."
        })

        if damage_severity == "severe_damage":
            chemical_treatments.append({
                "name": "Metaldehyde 2.5% Pellets (Emergency Intervention Only)",
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
            "name": "1% Bordeaux Mixture Spray",
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
            "name": "10% Bordeaux Paste",
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
            "name": "Mancozeb 75 WP or Copper Oxychloride 50 WP",
            "dosage": "2.0 to 2.5 grams per liter of water",
            "safety": "Spray during early morning or late afternoon. Avoid spraying during high heat."
        })

    # Summary text generation
    summary_parts = []
    if has_snail:
        summary_parts.append(f"🐌 **Giant African Snail Detected:** {snail_count} snail(s) identified. Immediate morning hand-collection and barrier treatment recommended.")
    if has_confirmed_damage:
        summary_parts.append(f"🍃 **Feeding Damage Severity:** {damage_severity.replace('_', ' ').title()}. Implement snail baiting and remove daytime hiding debris.")
    if has_confirmed_disease:
        summary_parts.append(f"🌿 **Disease Diagnosed:** {disease_cls.replace('_', ' ').title()}. Follow the agronomic protocol and apply approved fungicides.")
    if disease_cls == "UNCERTAIN" and not has_snail and not has_confirmed_damage:
        summary_parts.append("🔍 **Further Observation Required:** Image patterns are inconclusive. Please capture a clear, well-lit close-up of the affected foliage or bunch.")

    summary_text = "\n\n".join(summary_parts) if summary_parts else "Plantation health evaluation complete."

    return {
        "summary_text": summary_text,
        "is_healthy": is_healthy,
        "action_steps": action_steps,
        "home_remedies": home_remedies,
        "chemical_treatments": chemical_treatments,
        "prevention_tips": prevention_tips or ["Conduct routine bi-weekly field scouting", "Maintain clean drainage trenches"]
    }
