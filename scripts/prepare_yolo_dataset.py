import os
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISS_DIR = ROOT / "datasets" / "lissachatina-1.v3i.yolov8"
ARECA_DIR = ROOT / "datasets" / "arecanut_disease_split" / "train"
OUT_DIR = ROOT / "datasets" / "snail_yolo"
SEED = 42

def prepare_yolo():
    random.seed(SEED)
    print("Preparing YOLO Giant African Snail Dataset...")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    for split in ["train", "val", "test"]:
        (OUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    # 1. Validation split: copy all 1,177 images and labels
    src_val_imgs = sorted(list((LISS_DIR / "valid" / "images").glob("*.jpg")))
    src_val_lbls_dir = LISS_DIR / "valid" / "labels"
    print(f"Copying {len(src_val_imgs)} validation images...")
    for img in src_val_imgs:
        shutil.copy2(img, OUT_DIR / "images" / "val" / img.name)
        lbl = src_val_lbls_dir / f"{img.stem}.txt"
        if lbl.exists():
            shutil.copy2(lbl, OUT_DIR / "labels" / "val" / lbl.name)

    # 2. Test split: copy all 589 images and labels
    src_test_imgs = sorted(list((LISS_DIR / "test" / "images").glob("*.jpg")))
    src_test_lbls_dir = LISS_DIR / "test" / "labels"
    print(f"Copying {len(src_test_imgs)} test images...")
    for img in src_test_imgs:
        shutil.copy2(img, OUT_DIR / "images" / "test" / img.name)
        lbl = src_test_lbls_dir / f"{img.stem}.txt"
        if lbl.exists():
            shutil.copy2(lbl, OUT_DIR / "labels" / "test" / lbl.name)

    # 3. Training split: Sample 1,200 diverse snail images
    src_train_imgs = sorted(list((LISS_DIR / "train" / "images").glob("*.jpg")))
    src_train_lbls_dir = LISS_DIR / "train" / "labels"
    random.shuffle(src_train_imgs)
    sampled_train = src_train_imgs[:1200]
    print(f"Sampling {len(sampled_train)} diverse snail training images...")
    for img in sampled_train:
        shutil.copy2(img, OUT_DIR / "images" / "train" / img.name)
        lbl = src_train_lbls_dir / f"{img.stem}.txt"
        if lbl.exists():
            shutil.copy2(lbl, OUT_DIR / "labels" / "train" / lbl.name)

    # 4. Add plantation background images (negative samples)
    areca_imgs = []
    if ARECA_DIR.exists():
        for cat in ARECA_DIR.iterdir():
            if cat.is_dir():
                areca_imgs.extend(list(cat.glob("*.jpg")))
    random.shuffle(areca_imgs)
    sampled_bg = areca_imgs[:100]
    print(f"Adding {len(sampled_bg)} arecanut plantation background negative samples...")
    for img in sampled_bg:
        target_name = f"bg_{img.name}"
        shutil.copy2(img, OUT_DIR / "images" / "train" / target_name)
        # Empty label file for negative background
        lbl_target = OUT_DIR / "labels" / "train" / f"{Path(target_name).stem}.txt"
        lbl_target.write_text("", encoding="utf-8")

    # 5. Create data.yaml
    out_dir_str = str(OUT_DIR.resolve()).replace("\\", "/")
    yaml_content = f"""path: {out_dir_str}
train: images/train
val: images/val
test: images/test

nc: 1
names:
  0: giant_african_snail
"""
    (OUT_DIR / "data.yaml").write_text(yaml_content, encoding="utf-8")
    print(f"Wrote data.yaml to {OUT_DIR / 'data.yaml'}")
    print("YOLO dataset preparation complete!")

if __name__ == "__main__":
    prepare_yolo()
