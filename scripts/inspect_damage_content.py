from PIL import Image
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SNAIL_DIR = ROOT / "datasets" / "snail" / "snail dataset"

for cat in ["low damage", "medium damage", "highly damage"]:
    p = SNAIL_DIR / cat
    for img_path in sorted(p.glob("*.png")):
        im = Image.open(img_path).convert("RGB")
        arr = np.array(im)
        # Check non-black region
        non_zero = np.where(arr.mean(axis=2) > 15)
        if len(non_zero[0]) > 0:
            ymin, ymax = non_zero[0].min(), non_zero[0].max()
            xmin, xmax = non_zero[1].min(), non_zero[1].max()
            print(f"{cat} / {img_path.name}: Shape={arr.shape}, Active Content Box=[ymin={ymin}, ymax={ymax}, xmin={xmin}, xmax={xmax}]")
        else:
            print(f"{cat} / {img_path.name}: Black image")
