from pathlib import Path
import yaml
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
SNAIL = ROOT / "datasets" / "snail"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def load_yaml():
    candidates = list(SNAIL.rglob("data.yaml")) + list(SNAIL.rglob("data.yml"))
    if not candidates:
        print("No data.yaml found under datasets/snail.")
        return None, None
    path = candidates[0]
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    print(f"\nYAML: {path}")
    print("Class names:", data.get("names"))
    print("Declared nc:", data.get("nc"))
    return path, data

def main():
    if not SNAIL.exists():
        print(f"Missing folder: {SNAIL}")
        return
    yaml_path, cfg = load_yaml()
    print("\nImage/label inventory:")
    for split in ("train", "valid", "val", "test"):
        img_dirs = list(SNAIL.glob(f"{split}/images"))
        if not img_dirs:
            continue
        img_dir = img_dirs[0]
        label_dir = SNAIL / split / "labels"
        images = [p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXTS]
        labels = list(label_dir.glob("*.txt")) if label_dir.exists() else []
        label_stems = {p.stem for p in labels}
        missing = [p.name for p in images if p.stem not in label_stems]
        class_counts = Counter()
        invalid_lines = 0
        for label in labels:
            for line in label.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if not parts:
                    continue
                try:
                    cls = int(float(parts[0]))
                    vals = [float(x) for x in parts[1:]]
                    if len(vals) != 4 or not all(0 <= v <= 1 for v in vals):
                        invalid_lines += 1
                    class_counts[cls] += 1
                except Exception:
                    invalid_lines += 1
        print(f"\n{split}: {len(images)} images, {len(labels)} label files")
        print("  object counts by class ID:", dict(class_counts))
        print("  images without matching label file:", len(missing))
        if missing[:5]:
            print("  examples:", missing[:5])
        print("  invalid annotation lines:", invalid_lines)
    print("\nArecanut background images:")
    areca_dir = ROOT / "datasets" / "arecanut" / "images"
    if areca_dir.exists():
        print(sum(1 for p in areca_dir.rglob("*") if p.suffix.lower() in IMG_EXTS))
    else:
        print("No images folder yet. Create datasets/arecanut/images and add verified no-snail images.")

if __name__ == "__main__":
    main()
