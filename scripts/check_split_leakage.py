import hashlib
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
YOLO_DIR = ROOT / "datasets" / "lissachatina-1.v3i.yolov8"

def check_leakage():
    hashes_by_split = defaultdict(dict)
    
    for split in ["train", "valid", "test"]:
        img_dir = YOLO_DIR / split / "images"
        for img in img_dir.glob("*.jpg"):
            with open(img, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            hashes_by_split[split][img.name] = h

    train_hashes = set(hashes_by_split["train"].values())
    val_hashes = set(hashes_by_split["valid"].values())
    test_hashes = set(hashes_by_split["test"].values())

    tv_overlap = train_hashes.intersection(val_hashes)
    tt_overlap = train_hashes.intersection(test_hashes)
    vt_overlap = val_hashes.intersection(test_hashes)

    print(f"Train images: {len(hashes_by_split['train'])}, Unique hashes: {len(train_hashes)}")
    print(f"Val images: {len(hashes_by_split['valid'])}, Unique hashes: {len(val_hashes)}")
    print(f"Test images: {len(hashes_by_split['test'])}, Unique hashes: {len(test_hashes)}")
    print(f"Overlap Train & Val: {len(tv_overlap)}")
    print(f"Overlap Train & Test: {len(tt_overlap)}")
    print(f"Overlap Val & Test: {len(vt_overlap)}")

if __name__ == "__main__":
    check_leakage()
