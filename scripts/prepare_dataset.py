from pathlib import Path
import shutil
import yaml
import random
import re

ROOT = Path(__file__).resolve().parents[1]
SNAIL = ROOT / "datasets" / "snail"
ARECA_IMAGES = ROOT / "datasets" / "arecanut" / "images"
OUT = ROOT / "datasets" / "final"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
TARGET_CLASS_NAME = None  # Set exact name from data.yaml if multiple classes exist.
SEED = 42

def names_to_dict(names):
    if isinstance(names, list):
        return {i: str(n) for i, n in enumerate(names)}
    if isinstance(names, dict):
        return {int(k): str(v) for k, v in names.items()}
    return {}

def find_yaml():
    paths = list(SNAIL.rglob("data.yaml")) + list(SNAIL.rglob("data.yml"))
    if not paths:
        raise FileNotFoundError("Could not find data.yaml under datasets/snail")
    return paths[0]

def locate_split(split_names):
    for split in split_names:
        image_dir = SNAIL / split / "images"
        label_dir = SNAIL / split / "labels"
        if image_dir.exists() and label_dir.exists():
            return split, image_dir, label_dir
    return None, None, None

def safe_name(path, prefix):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem)
    return f"{prefix}_{cleaned}{path.suffix.lower()}"

def main():
    yaml_path = find_yaml()
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    names = names_to_dict(cfg.get("names"))
    if not names:
        raise ValueError("No class names found in data.yaml.")
    print("Classes found:", names)

    if TARGET_CLASS_NAME:
        matches = [i for i, n in names.items() if n == TARGET_CLASS_NAME]
        if len(matches) != 1:
            raise ValueError(f"TARGET_CLASS_NAME {TARGET_CLASS_NAME!r} not found exactly once.")
        target_id = matches[0]
    elif len(names) == 1:
        target_id = next(iter(names))
    else:
        raise ValueError(
            "Dataset has multiple classes. Set TARGET_CLASS_NAME at top of this script "
            "to the exact Giant African Snail class name shown above."
        )

    random.seed(SEED)
    for p in OUT.rglob("*"):
        if p.is_file():
            p.unlink()
    for split in ("train", "val", "test"):
        (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

    split_map = {
        "train": ("train",),
        "val": ("valid", "val"),
        "test": ("test",)
    }
    copied = {k: 0 for k in split_map}
    for out_split, source_names in split_map.items():
        source_split, image_dir, label_dir = locate_split(source_names)
        if not image_dir:
            if out_split == "test":
                print("No test split found in source; skipping.")
                continue
            raise FileNotFoundError(f"Could not find images/labels for {out_split} in {source_names}")
        for image in image_dir.iterdir():
            if image.suffix.lower() not in IMG_EXTS:
                continue
            label = label_dir / f"{image.stem}.txt"
            if not label.exists():
                print(f"Skipping image with no label file: {image.name}")
                continue
            new_image = safe_name(image, "snail")
            new_label = Path(new_image).with_suffix(".txt")
            out_img = OUT / "images" / out_split / new_image
            out_lbl = OUT / "labels" / out_split / new_label
            kept_lines = []
            for line in label.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if not parts:
                    continue
                cls = int(float(parts[0]))
                if cls == target_id:
                    parts[0] = "0"
                    kept_lines.append(" ".join(parts))
            shutil.copy2(image, out_img)
            out_lbl.write_text("\n".join(kept_lines), encoding="utf-8")
            copied[out_split] += 1

    # Add only verified no-snail arecanut photos to train as empty-label negatives.
    if ARECA_IMAGES.exists():
        for image in ARECA_IMAGES.rglob("*"):
            if image.suffix.lower() not in IMG_EXTS:
                continue
            new_image = safe_name(image, "areca_negative")
            shutil.copy2(image, OUT / "images" / "train" / new_image)
            (OUT / "labels" / "train" / Path(new_image).with_suffix(".txt")).write_text("", encoding="utf-8")
            copied["train"] += 1

    data = {
        "path": str(OUT.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "names": {0: "giant_african_snail"}
    }
    if any((OUT / "images" / "test").iterdir()):
        data["test"] = "images/test"
    (OUT / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print("\nPrepared dataset counts:", copied)
    print("Wrote:", OUT / "data.yaml")
    print("Review all images/labels and ensure the validation set has enough positive snail examples.")
    print("Do not treat generic snail images as verified arecanut-plantation images.")

if __name__ == "__main__":
    main()
