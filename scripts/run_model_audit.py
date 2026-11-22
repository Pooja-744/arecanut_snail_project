"""
Model Validation and Performance Audit Script.
Tests all 7 scenarios against the multi-task inference pipeline:
  1. Snail-only images
  2. Snail with visible feeding damage
  3. Snail without visible feeding damage
  4. Healthy arecanut leaves
  5. Healthy arecanut nuts
  6. Genuine disease images (Bud Rot, Koleroga, Yellow Leaf, Ring Spot)
  7. Unclear / out-of-domain images
Saves actual evaluated metrics to results/model_evaluation_audit.json.
"""
import json
import time
import sys
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.inference import analyze_image, _ensure_loaded
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def create_unclear_image(path: Path):
    """Create an artificial out-of-domain test image (low-contrast gray noise)."""
    arr = np.full((128, 128, 3), 128, dtype=np.uint8)
    # Add subtle low noise
    noise = np.random.randint(-3, 3, (128, 128, 3), dtype=np.int16)
    arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr)
    im.save(path)
    return path

def main():
    print("=" * 75)
    print("ARECANUT & SNAIL SURVEILLANCE SYSTEM — PERFORMANCE AUDIT")
    print("=" * 75)

    _ensure_loaded()

    # Define test samples
    test_cases = [
        # 1. Snail-only (snail on bark/trunk without foliar feeding damage)
        {
            "scenario": "1. Snail-only",
            "path": ROOT / "datasets" / "snail" / "snail dataset" / "snail in arecanut" / "Screenshot 2026-09-18 211252.png",
            "expected_snail": True,
            "expected_damage": False
        },
        # 2. Snail with visible feeding damage
        {
            "scenario": "2. Snail with visible feeding damage",
            "path": ROOT / "datasets" / "damage_dataset" / "severe_damage" / "severe_damage_001.jpg",
            "expected_snail": False, # Damage patch
            "expected_damage": True
        },
        # 3. Snail without visible feeding damage
        {
            "scenario": "3. Snail without visible feeding damage",
            "path": ROOT / "datasets" / "snail" / "snail dataset" / "snail in arecanut" / "Screenshot 2026-09-18 212925.png",
            "expected_snail": True,
            "expected_damage": False
        },
        # 4. Healthy arecanut leaves
        {
            "scenario": "4. Healthy arecanut leaves",
            "path": ROOT / "datasets" / "arecanut" / "images" / "HEALTHY LEAF" / "Healthy leaf(1).jpeg",
            "expected_snail": False,
            "expected_damage": False
        },
        # 5. Healthy arecanut nuts
        {
            "scenario": "5. Healthy arecanut nuts",
            "path": ROOT / "datasets" / "arecanut" / "images" / "HEALTHY NUT" / "healthy_nut (1).jpeg",
            "expected_snail": False,
            "expected_damage": False
        },
        # 6. Genuine disease images
        {
            "scenario": "6a. Genuine disease — Bud Rot",
            "path": ROOT / "datasets" / "arecanut" / "images" / "BUD ROT" / "bud rot 4.jpg",
            "expected_snail": False,
            "expected_disease": "BUD ROT"
        },
        {
            "scenario": "6b. Genuine disease — Koleroga",
            "path": ROOT / "datasets" / "arecanut" / "images" / "KOLEROGA" / "MahaliKoleroga (181).jpg",
            "expected_snail": False,
            "expected_disease": "KOLEROGA"
        },
        {
            "scenario": "6c. Genuine disease — Yellow Leaf",
            "path": ROOT / "datasets" / "arecanut" / "images" / "YELLOW LEAF" / "IMG-20240427-WA0026.jpg",
            "expected_snail": False,
            "expected_disease": "YELLOW LEAF"
        },
        {
            "scenario": "6d. Genuine disease — Ring Spot",
            "path": ROOT / "datasets" / "arecanut" / "images" / "RING SPOT" / "download (1).jpg",
            "expected_snail": False,
            "expected_disease": "RING SPOT"
        },
        # 7. Unclear and non-arecanut images
        {
            "scenario": "7. Unclear / non-arecanut image",
            "path": ROOT / "test_images" / "unclear_blank_sample.jpg",
            "expected_overall": "further_inspection"
        }
    ]

    # Create unclear test image if needed
    create_unclear_image(ROOT / "test_images" / "unclear_blank_sample.jpg")

    audit_results = []
    
    for tc in test_cases:
        p = tc["path"]
        if not p.exists():
            print(f"Skipping {tc['scenario']}: file not found {p}")
            continue

        im = Image.open(p).convert("RGB")
        res = analyze_image(im)

        snail_res = res["snail_detection"]
        disease_res = res["disease_classification"]
        damage_res = res["damage_assessment"]
        overall_status = res["overall_status"]
        overall_text = res["overall_status_text"]

        record = {
            "scenario": tc["scenario"],
            "image": p.name,
            "overall_status": overall_status,
            "overall_status_text": overall_text,
            "snail_detected": snail_res["detected"],
            "snail_count": snail_res["count"],
            "snail_confidence": snail_res["confidence"],
            "disease_class": disease_res["predicted_class"],
            "disease_confidence": disease_res["confidence"],
            "is_healthy": disease_res["is_healthy"],
            "has_damage": damage_res["has_damage"],
            "damage_severity": damage_res["severity"],
            "damage_confidence": damage_res["confidence"],
        }
        audit_results.append(record)

        print(f"\n--- {tc['scenario']} ({p.name}) ---")
        print(f"  Overall Status:      {overall_status} ({overall_text})")
        print(f"  Snail Detection:     detected={snail_res['detected']} count={snail_res['count']} conf={snail_res['confidence']}")
        print(f"  Disease Diagnosis:   {disease_res['predicted_class']} (conf={disease_res['confidence']}) is_healthy={disease_res['is_healthy']}")
        print(f"  Feeding Damage:      has_damage={damage_res['has_damage']} severity={damage_res['severity']} conf={damage_res['confidence']}")

    out_file = RESULTS_DIR / "model_evaluation_audit.json"
    with open(out_file, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "audit_cases_count": len(audit_results),
            "results": audit_results
        }, f, indent=2)

    print("\n" + "=" * 75)
    print(f"Audit completed successfully. Results saved to: {out_file}")
    print("=" * 75)

if __name__ == "__main__":
    main()
