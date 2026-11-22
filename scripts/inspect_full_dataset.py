import os
import sys
import hashlib
import struct
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT / "datasets"

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif', '.gif'}

def get_image_size(file_path):
    """
    Pure Python image dimension reader for JPEG, PNG, GIF, BMP, WEBP.
    Falls back to None if unreadable.
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read(65536)
            size = len(data)
            if size < 8:
                return None, "Corrupted/Too small (<8 bytes)"

            # PNG
            if data.startswith(b'\x89PNG\r\n\x1a\n') and size >= 24:
                w, h = struct.unpack('>LL', data[16:24])
                return (int(w), int(h), 'PNG'), None

            # GIF
            if data[:6] in (b'GIF87a', b'GIF89a') and size >= 10:
                w, h = struct.unpack('<HH', data[6:10])
                return (int(w), int(h), 'GIF'), None

            # BMP
            if data.startswith(b'BM') and size >= 26:
                w, h = struct.unpack('<LL', data[18:26])
                return (int(w), int(h), 'BMP'), None

            # WEBP
            if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
                if data[12:16] == b'VP8 ' and size >= 30:
                    w, h = struct.unpack('<HH', data[26:30])
                    return (int(w & 0x3fff), int(h & 0x3fff), 'WEBP'), None
                elif data[12:16] == b'VP8L' and size >= 25:
                    b1, b2, b3, b4 = struct.unpack('<BBBB', data[21:25])
                    w = 1 + (((b2 & 0x3f) << 8) | b1)
                    h = 1 + (((b4 & 0xf) << 10) | (b3 << 2) | ((b2 & 0xc0) >> 6))
                    return (int(w), int(h), 'WEBP'), None
                elif data[12:16] == b'VP8X' and size >= 30:
                    w = 1 + struct.unpack('<I', data[24:27] + b'\x00')[0]
                    h = 1 + struct.unpack('<I', data[27:30] + b'\x00')[0]
                    return (int(w), int(h), 'WEBP'), None

            # JPEG
            if data.startswith(b'\xff\xd8'):
                f.seek(0)
                full_data = f.read()
                offset = 2
                while offset < len(full_data):
                    if full_data[offset] != 0xff:
                        offset += 1
                        continue
                    marker = full_data[offset + 1]
                    # SOF markers: 0xC0 to 0xCF except 0xC4, 0xC8, 0xCC
                    if marker in [0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]:
                        h, w = struct.unpack('>HH', full_data[offset + 5:offset + 9])
                        return (int(w), int(h), 'JPEG'), None
                    elif marker in (0xd9, 0xda):  # EOI or SOS
                        break
                    elif marker == 0xd8:  # SOI
                        offset += 2
                    else:
                        length = struct.unpack('>H', full_data[offset + 2:offset + 4])[0]
                        offset += 2 + length
                return None, "JPEG SOF marker not found"
            
            return None, "Unknown image format"
    except Exception as e:
        return None, str(e)

def get_file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def scan_all():
    print("=" * 80)
    print("DATASET INSPECTION SUITE: SCANNING DIRECTORIES")
    print("=" * 80)

    # 1. Directory Tree & Counts
    categories = defaultdict(list)
    corrupted_files = []
    exact_duplicates = defaultdict(list)
    format_counts = Counter()
    resolutions = Counter()
    aspect_ratios = Counter()

    for p in DATASETS_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            rel = p.relative_to(DATASETS_DIR)
            top_cat = rel.parts[0]
            categories[str(rel.parent)].append(p)
            format_counts[p.suffix.lower()] += 1

            # Hash check
            fhash = get_file_hash(p)
            exact_duplicates[fhash].append(p)

            # Size & dimension check
            size_info, err = get_image_size(p)
            if err:
                corrupted_files.append((p, err))
            else:
                w, h, fmt = size_info
                resolutions[f"{w}x{h}"] += 1
                ar = round(w / h, 2) if h > 0 else 0
                aspect_ratios[ar] += 1

    print("\n--- Summary by Subfolder ---")
    total_imgs = sum(len(v) for v in categories.items()) # wait, total files:
    total_imgs = sum(len(v) for v in categories.values())
    print(f"Total image files found across all subfolders: {total_imgs}")
    for folder, files in sorted(categories.items()):
        print(f"  {folder}: {len(files)} images")

    print("\n--- Format Distribution ---")
    for fmt, count in format_counts.most_common():
        print(f"  {fmt}: {count} ({count/total_imgs*100:.1f}%)")

    print(f"\n--- Corrupted / Unreadable Images ---")
    print(f"  Total corrupted: {len(corrupted_files)}")
    for p, err in corrupted_files[:10]:
        print(f"    {p.relative_to(ROOT)}: {err}")

    # Duplicates
    dup_groups = {k: v for k, v in exact_duplicates.items() if len(v) > 1}
    total_duplicate_files = sum(len(v) - 1 for v in dup_groups.values())
    print(f"\n--- Exact Duplicate Analysis ---")
    print(f"  Total unique images: {len(exact_duplicates)}")
    print(f"  Duplicate groups: {len(dup_groups)}")
    print(f"  Total redundant duplicate files: {total_duplicate_files}")
    for k, v in list(dup_groups.items())[:5]:
        print(f"    Group (SHA256 {k[:8]}...): {[str(p.relative_to(ROOT)) for p in v]}")

    print("\n--- Most Common Resolutions (Top 10) ---")
    for res, cnt in resolutions.most_common(10):
        print(f"  {res}: {cnt} images ({cnt/total_imgs*100:.1f}%)")

    # 2. Check YOLO Annotations in lissachatina
    print("\n" + "=" * 80)
    print("YOLO ANNOTATION INSPECTION (datasets/lissachatina-1.v3i.yolov8)")
    print("=" * 80)
    yolo_dir = DATASETS_DIR / "lissachatina-1.v3i.yolov8"
    if yolo_dir.exists():
        for split in ["train", "valid", "test"]:
            s_img_dir = yolo_dir / split / "images"
            s_lbl_dir = yolo_dir / split / "labels"
            if not s_img_dir.exists():
                print(f"Split {split}: Missing images folder")
                continue
            s_imgs = [p for p in s_img_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS]
            s_lbls = list(s_lbl_dir.glob("*.txt")) if s_lbl_dir.exists() else []
            s_lbl_map = {p.stem: p for p in s_lbls}
            
            missing_labels = [p.name for p in s_imgs if p.stem not in s_lbl_map]
            empty_labels = []
            box_counts = []
            class_counts = Counter()
            out_of_bounds_boxes = 0

            for img in s_imgs:
                lbl = s_lbl_map.get(img.stem)
                if not lbl:
                    continue
                content = lbl.read_text(encoding="utf-8").strip()
                if not content:
                    empty_labels.append(lbl.name)
                    box_counts.append(0)
                    continue
                lines = content.splitlines()
                box_counts.append(len(lines))
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            cls_id = int(parts[0])
                            x, y, w, h = map(float, parts[1:5])
                            class_counts[cls_id] += 1
                            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                                out_of_bounds_boxes += 1
                        except:
                            out_of_bounds_boxes += 1

            print(f"Split: '{split}'")
            print(f"  Images: {len(s_imgs)}")
            print(f"  Label files: {len(s_lbls)}")
            print(f"  Images missing label file: {len(missing_labels)}")
            print(f"  Images with 0 bounding boxes (empty background): {len(empty_labels)}")
            print(f"  Total bounding boxes: {sum(box_counts)}")
            print(f"  Class distribution: {dict(class_counts)}")
            print(f"  Invalid / Out of bounds boxes: {out_of_bounds_boxes}")
            if box_counts:
                print(f"  Avg boxes per image: {sum(box_counts)/len(box_counts):.2f} (Max: {max(box_counts)})")

    # 3. Check 'snail dataset' (snail in arecanut, damage severity)
    print("\n" + "=" * 80)
    print("INSPECTION OF datasets/snail/snail dataset")
    print("=" * 80)
    snail_dataset_dir = DATASETS_DIR / "snail" / "snail dataset"
    if snail_dataset_dir.exists():
        for sub in snail_dataset_dir.iterdir():
            if sub.is_dir():
                sub_imgs = [p for p in sub.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
                sub_txts = [p for p in sub.rglob("*.txt") if p.is_file()]
                sub_xmls = [p for p in sub.rglob("*.xml") if p.is_file()]
                sub_jsons = [p for p in sub.rglob("*.json") if p.is_file()]
                print(f"Subcategory: '{sub.name}'")
                print(f"  Image count: {len(sub_imgs)}")
                print(f"  Annotations found: txt={len(sub_txts)}, xml={len(sub_xmls)}, json={len(sub_jsons)}")
                # Sample dimensions
                sub_res = Counter()
                for img in sub_imgs[:50]:
                    s, _ = get_image_size(img)
                    if s:
                        sub_res[f"{s[0]}x{s[1]}"] += 1
                print(f"  Sample resolutions: {dict(sub_res.most_common(3))}")

    # 4. Check 'arecanut' images (diseases and healthy)
    print("\n" + "=" * 80)
    print("INSPECTION OF datasets/arecanut/images (Disease & Healthy Categories)")
    print("=" * 80)
    areca_dir = DATASETS_DIR / "arecanut" / "images"
    if areca_dir.exists():
        for sub in areca_dir.iterdir():
            if sub.is_dir():
                sub_imgs = [p for p in sub.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
                print(f"Category: '{sub.name}' -> {len(sub_imgs)} images")

    print("\n" + "=" * 80)
    print("END OF PRELIMINARY INSPECTION")
    print("=" * 80)

if __name__ == "__main__":
    scan_all()
