from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAIL_DIR = ROOT / "datasets" / "snail" / "snail dataset"

for cat in SNAIL_DIR.iterdir():
    if cat.is_dir():
        imgs = list(cat.glob("*"))
        print(f"\nCategory: {cat.name} ({len(imgs)} items)")
        for img in sorted(imgs):
            size_kb = img.stat().st_size / 1024
            print(f"  - {img.name} ({size_kb:.1f} KB)")
