import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "datasets" / "snail" / "snail dataset"
DEST_DIR = ROOT / "datasets" / "damage_dataset"

mapping = {
    "low damage": "low_damage",
    "medium damage": "moderate_damage",
    "highly damage": "severe_damage"
}

for src_name, dest_name in mapping.items():
    s_path = SRC_DIR / src_name
    d_path = DEST_DIR / dest_name
    d_path.mkdir(parents=True, exist_ok=True)
    if s_path.exists():
        for img in s_path.glob("*.png"):
            # Convert to standard RGB JPEG
            with Image.open(img) as im:
                rgb = im.convert("RGB")
                rgb.save(d_path / f"orig_{img.stem}.jpg", "JPEG", quality=95)
            print(f"Copied {img.name} -> {d_path.name}")

print("\nDamage dataset structure initialized at: datasets/damage_dataset")
