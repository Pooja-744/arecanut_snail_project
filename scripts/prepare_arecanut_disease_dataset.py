import os
import shutil
import hashlib
from pathlib import Path
from collections import defaultdict
import random

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "datasets" / "arecanut" / "images"
DEST_DIR = ROOT / "datasets" / "arecanut_disease_split"
SEED = 42

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def prepare_splits():
    random.seed(SEED)
    print("Preparing Arecanut Disease & Health Dataset with 70/20/10 Split...")
    
    if not SRC_DIR.exists():
        raise FileNotFoundError(f"Source folder not found: {SRC_DIR}")

    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)

    categories = [d for d in SRC_DIR.iterdir() if d.is_dir()]
    print(f"Discovered {len(categories)} categories:")

    split_stats = {
        "train": defaultdict(int),
        "val": defaultdict(int),
        "test": defaultdict(int)
    }

    dedup_removed = 0

    for cat_dir in sorted(categories):
        cat_name = cat_dir.name
        images = [p for p in cat_dir.iterdir() if p.is_file() and p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}]
        
        # Deduplication check
        seen_hashes = {}
        unique_images = []
        for img in images:
            h = sha256_file(img)
            if h in seen_hashes:
                print(f"  [Deduplication] Removing duplicate in {cat_name}: {img.name} (matches {seen_hashes[h].name})")
                dedup_removed += 1
            else:
                seen_hashes[h] = img
                unique_images.append(img)

        # Shuffle deterministically
        random.shuffle(unique_images)
        total = len(unique_images)
        
        # 70% Train, 20% Val, 10% Test
        n_train = int(round(total * 0.70))
        n_val = int(round(total * 0.20))
        n_test = total - n_train - n_val

        train_imgs = unique_images[:n_train]
        val_imgs = unique_images[n_train:n_train + n_val]
        test_imgs = unique_images[n_train + n_val:]

        for split, split_files in [("train", train_imgs), ("val", val_imgs), ("test", test_imgs)]:
            target_folder = DEST_DIR / split / cat_name
            target_folder.mkdir(parents=True, exist_ok=True)
            for f in split_files:
                shutil.copy2(f, target_folder / f.name)
                split_stats[split][cat_name] += 1

        print(f"  - {cat_name}: {total} unique images -> Train: {n_train}, Val: {n_val}, Test: {n_test}")

    print("\nSplit preparation complete!")
    print(f"Total duplicate files safely excluded: {dedup_removed}")
    print(f"Destination folder: {DEST_DIR.relative_to(ROOT)}")
    for split in ["train", "val", "test"]:
        total_split = sum(split_stats[split].values())
        print(f"  {split.upper()} total: {total_split} images")

if __name__ == "__main__":
    prepare_splits()
