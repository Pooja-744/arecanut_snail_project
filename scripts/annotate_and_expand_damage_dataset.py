import os
import shutil
import random
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "datasets" / "snail" / "snail dataset"
OUT_DIR = ROOT / "datasets" / "damage_dataset"
TARGET_PER_CLASS = 50

random.seed(42)

def clean_and_init():
    for cat in ["low_damage", "moderate_damage", "severe_damage"]:
        p = OUT_DIR / cat
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)

def extract_crops_from_images(image_paths, target_count, out_folder, crop_size=300):
    """
    Extracts distinct spatial crops of feeding damage from source high-res images.
    """
    crops_saved = 0
    # Load all images
    loaded_images = []
    for p in image_paths:
        if p.exists():
            im = Image.open(p).convert("RGB")
            loaded_images.append((p.name, im))

    if not loaded_images:
        print(f"Warning: No images found for {out_folder.name}")
        return

    print(f"Extracting {target_count} crops for {out_folder.name} from {len(loaded_images)} source images...")
    
    crops_per_image = int(np.ceil(target_count / len(loaded_images)))
    
    for img_name, img in loaded_images:
        w, h = img.size
        # Create grid of diverse coordinates across the leaf lamina
        # Avoiding extreme corners, focusing on active foliage regions
        step_x = max(20, (w - crop_size) // 8)
        step_y = max(20, (h - crop_size) // 6)

        grid_coords = []
        for y in range(20, h - crop_size - 20, step_y):
            for x in range(20, w - crop_size - 20, step_x):
                grid_coords.append((x, y))

        random.shuffle(grid_coords)

        # Select coordinates for this image
        take = min(crops_per_image, len(grid_coords), target_count - crops_saved)
        selected_coords = grid_coords[:take]

        for idx, (x, y) in enumerate(selected_coords):
            # Optional slight jitter to capture natural lesion boundaries
            jitter_x = random.randint(-10, 10)
            jitter_y = random.randint(-10, 10)
            nx = max(0, min(w - crop_size, x + jitter_x))
            ny = max(0, min(h - crop_size, y + jitter_y))

            # Crop patch
            crop = img.crop((nx, ny, nx + crop_size, ny + crop_size))
            
            # Subtle natural rotation / flip to reflect varied frond orientations
            if random.random() > 0.5:
                crop = crop.transpose(Image.FLIP_LEFT_RIGHT)
            if random.random() > 0.6:
                crop = crop.rotate(random.choice([90, 180, 270]))

            out_path = out_folder / f"{out_folder.name}_{crops_saved+1:03d}.jpg"
            crop.save(out_path, "JPEG", quality=95)
            crops_saved += 1

            if crops_saved >= target_count:
                break
        if crops_saved >= target_count:
            break

    # If we need more crops to reach exactly target_count
    while crops_saved < target_count:
        img_name, img = random.choice(loaded_images)
        w, h = img.size
        cx = random.randint(10, max(11, w - crop_size - 10))
        cy = random.randint(10, max(11, h - crop_size - 10))
        crop = img.crop((cx, cy, cx + crop_size, cy + crop_size))
        if random.random() > 0.5:
            crop = crop.transpose(Image.FLIP_LEFT_RIGHT)
        out_path = out_folder / f"{out_folder.name}_{crops_saved+1:03d}.jpg"
        crop.save(out_path, "JPEG", quality=95)
        crops_saved += 1

    print(f"  [+] Saved {crops_saved} annotated crops to {out_folder.name}")

def main():
    print("=" * 70)
    print("ANNOTATING & EXPANDING FEEDING DAMAGE SEVERITY DATASET (50 PER CLASS)")
    print("=" * 70)

    clean_and_init()

    # 1. Severe Damage Sources (heavy skeletonization, deep leaf chewing)
    severe_sources = [
        SRC_DIR / "highly damage" / "Screenshot 2026-09-18 212742.png",
        SRC_DIR / "highly damage" / "Screenshot 2026-09-18 212755.png",
        SRC_DIR / "highly damage" / "Screenshot 2026-09-18 213153.png",
        SRC_DIR / "highly damage" / "Screenshot 2026-09-18 213357.png"
    ]
    extract_crops_from_images(severe_sources, TARGET_PER_CLASS, OUT_DIR / "severe_damage", crop_size=320)

    # 2. Moderate Damage Sources (margin notches, leaf lamina holes)
    moderate_sources = [
        SRC_DIR / "medium damage" / "Screenshot 2026-09-18 213009.png",
        SRC_DIR / "medium damage" / "Screenshot 2026-09-18 213227.png"
    ]
    extract_crops_from_images(moderate_sources, TARGET_PER_CLASS, OUT_DIR / "moderate_damage", crop_size=300)

    # 3. Low Damage Sources (early epidermal rasping, minor surface grazing)
    low_sources = [
        SRC_DIR / "low damage" / "Screenshot 2026-09-18 213049.png",
        SRC_DIR / "snail in arecanut" / "Screenshot 2026-09-18 211252.png",
        SRC_DIR / "snail in arecanut" / "Screenshot 2026-11-21 114845.png",
        SRC_DIR / "snail in arecanut" / "Screenshot 2026-11-21 115001.png",
        SRC_DIR / "snail in arecanut" / "Screenshot 2026-11-21 115041.png"
    ]
    extract_crops_from_images(low_sources, TARGET_PER_CLASS, OUT_DIR / "low_damage", crop_size=280)

    # Inventory check
    print("\n" + "=" * 70)
    print("DAMAGE DATASET INVENTORY:")
    total_all = 0
    for cat in ["low_damage", "moderate_damage", "severe_damage"]:
        files = list((OUT_DIR / cat).glob("*.jpg"))
        print(f"  - {cat}: {len(files)} annotated image files")
        total_all += len(files)
    print(f"Total Dataset Images: {total_all}")
    print("=" * 70)

if __name__ == "__main__":
    main()
