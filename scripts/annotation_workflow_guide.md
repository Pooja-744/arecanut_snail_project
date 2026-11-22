# Giant African Snail & Plantation Damage Annotation Workflow Guide

This document outlines the standardized protocol for generating YOLO-compatible object detection bounding boxes and severity classification labels for unannotated plantation images.

---

## 1. Context & Dataset Status

During the automated dataset inspection, the following unannotated images were identified:
- **`datasets/snail/snail dataset/snail in arecanut` (17 images):** In-situ photographs of Giant African Snails (*Lissachatina fulica*) on arecanut trunks, leaves, and plantation ground. Currently missing bounding box labels (`.txt` YOLO files).
- **`datasets/snail/snail dataset/{low damage, medium damage, highly damage}` (7 images):** Feeding damage photographs on arecanut foliage. Currently insufficient for deep CNN training (minimum 50–100 samples per severity class required).

---

## 2. Option A: Annotation with CVAT (Computer Vision Annotation Tool)

CVAT is an open-source, web-based annotation platform suitable for academic and local deployment.

### Step 1: Project & Label Setup
1. Open CVAT ([cvat.ai](https://app.cvat.ai) or local Docker instance).
2. Create a new Project named `Arecanut_Giant_African_Snail`.
3. Add a single detection label:
   - **Label Name:** `giant_african_snail`
   - **Type:** Rectangle (Bounding Box)
   - *Note:* Do not create separate classes for host plants (e.g., `snail_on_trunk`, `snail_on_leaf`). The host context is learned implicitly as background.

### Step 2: Image Upload & Bounding Box Guidelines
1. Upload the unannotated images from `datasets/snail/snail dataset/snail in arecanut/`.
2. Tight Bounding Boxes: Draw the rectangle tightly around the snail shell and extended body (foot/tentacles). Do not include large margins of tree bark.
3. Occlusions: If a snail is partially occluded behind a frond or nut bunch, enclose only the visible portion of the snail.
4. Small Snails: Zoom in (200%–400%) on whole-tree plantation images to locate juvenile or distant snails.
5. Multiple Snails: Annotate each individual snail with a separate bounding box to enable accurate counting.

### Step 3: Export in YOLO 1.1 Format
1. Click **Menu -> Export Task Dataset**.
2. Select format: **YOLO 1.1**.
3. Download the resulting zip archive containing:
   - `images/`: the image files.
   - `labels/`: `.txt` files containing `<class_id> <x_center> <y_center> <width> <height>` (all normalized between 0.0 and 1.0).

---

## 3. Option B: Annotation with Roboflow

Roboflow provides an intuitive annotation interface with automated YOLOv8 export.

### Step 1: Project Creation
1. Log in to [Roboflow](https://roboflow.com).
2. Click **Create New Project**.
3. Project Name: `arecanut-snail-detection`.
4. Project Type: **Object Detection**.
5. Annotation Group / Label: `giant_african_snail`.

### Step 2: Upload & Labeling
1. Drag and drop the 17 `snail in arecanut` images into the upload area.
2. Label each snail with the shortcut key `W` (Bounding Box) and assign `giant_african_snail`.
3. If no snail is present (negative background image), mark the image as a background sample with 0 annotations.

### Step 3: Train / Val / Test Split & Export
1. Set the dataset split to 70% Train, 20% Valid, 10% Test.
2. Under Preprocessing: Auto-orient and resize to 640x640 (Stretch or Fit with black borders).
3. Under Augmentation: Minimal augmentation (Horizontal Flip, ±15° Rotation, 10% Brightness variation). Avoid heavy shear or distortion.
4. Click **Generate Version** -> **Export Dataset** -> Format: **YOLOv8 PyTorch**.
5. Extract the exported zip directly into `datasets/snail_annotated/`.

---

## 4. Validating Newly Generated Labels

After exporting new annotations, run the project validation script:

```powershell
python scripts/inspect_data.py
```

The script will verify:
- Matching image and label stems.
- Coordinate validity (all values between 0.0 and 1.0).
- Absence of corrupted lines or negative values.
