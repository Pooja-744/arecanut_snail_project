# Arecanut Plantation Health & Giant African Snail Surveillance System

An academic research-grade deep learning system for **Giant African Snail (*Lissachatina fulica*) detection & counting**, **Arecanut plant disease classification**, and **Snail feeding damage severity classification**, optimized for deployment in real arecanut plantation environments.

---

## 1. Project Overview & Multi-Task Models

This system integrates three computer vision components:

1. **Giant African Snail Detection & Counting (Ultralytics YOLOv8n):**
   - Single unified class: `giant_african_snail`.
   - Trained with transfer learning and plantation background negative samples.
   - **Performance on 589 Unseen Test Images:**
     - **mAP@50:** **93.85%**
     - **Precision:** **91.89%**
     - **Recall:** **88.45%**
     - **mAP@50-95:** **60.27%**
     - **Inference Latency:** **~60.8 ms / image** (CPU)
   - Tested on 17 real plantation photos: detected snails in 11/17 images (16 total snails identified).
   - Saved weights: `models/snail_detection_best.pt`

2. **Arecanut Disease & Health Classification (MobileNetV2):**
   - Fine-tuned transfer learning on 6 verified plantation classes:
     - `BUD ROT` (Fungal rot)
     - `HEALTHY LEAF`
     - `HEALTHY NUT`
     - `KOLEROGA` (Fruit rot / Mahali disease)
     - `RING SPOT`
     - `YELLOW LEAF` (Yellow Leaf Disease - YLD)
   - **Performance on Unseen Test Dataset (29 images across 6 classes):**
     - **Overall Accuracy:** **96.55%**
     - **Macro F1-Score:** **0.97**
     - **Weighted F1-Score:** **0.97**
   - Saved weights: `models/arecanut_disease_best.pt`

3. **Snail Feeding Damage Severity Classification (MobileNetV2):**
   - Three severity classes: `low_damage`, `moderate_damage`, `severe_damage`.
   - An interactive **Damage Annotation Studio** is built into the web app to crop, tag, and expand the dataset towards 50–100 samples per class.
   - Initialized at: `datasets/damage_dataset/{low_damage, moderate_damage, severe_damage}`.
   - Train with one click in the web UI or via: `python scripts/train_damage_classifier.py`.
   - When trained, weights are saved to: `models/snail_damage_best.pt` and auto-loaded into the live inference pipeline.

---

## 2. Directory Structure

```text
Arecanut_snail_project/
├── backend/                           # Production FastAPI Enterprise Backend
│   ├── main.py                        # FastAPI application entry point & static frontend server
│   ├── core/
│   │   ├── config.py                  # Environment settings & model paths
│   │   ├── inference.py               # Integrated multi-model inference engine (YOLOv8 + 2x MobileNetV2)
│   │   └── supabase_client.py         # Supabase client singleton
│   ├── api/
│   │   ├── analysis.py                # Single-upload multi-model inference endpoint (/api/analysis)
│   │   ├── auth.py                    # User authentication & registration
│   │   ├── history.py                 # Past scan retrieval & pagination
│   │   ├── dashboard.py               # Aggregated plantation health metrics
│   │   ├── chatbot.py                 # Multilingual Kisan AI Chatbot (English & Kannada)
│   │   └── reports.py                 # Automated PDF Prescription & Report generator (/api/reports)
│   └── knowledge/
│       └── plantation_advisory.py     # ICAR & CPCRI grounded agronomic knowledge base
├── frontend/                          # Modern React + Vite Responsive Application
│   ├── src/
│   │   ├── App.jsx                    # Multi-tab UI (AI Vision, Chatbot, Metrics, Field Manual)
│   │   ├── index.css                  # Custom green plantation theme & badges
│   │   └── main.jsx
│   ├── dist/                          # Production built bundle (served automatically by backend)
│   └── package.json
├── app.py                             # Lightweight Flask Prototype (Dashboard & Crop Studio)
├── templates/
│   └── index.html                     # Bootstrap 5 responsive UI
├── models/
│   ├── snail_detection_best.pt        # Trained Champion YOLOv8n Snail Detection Model (93.8% mAP)
│   ├── arecanut_disease_best.pt       # Trained MobileNetV2 Disease Classification Model (96.5% Acc)
│   └── snail_damage_best.pt           # Trained MobileNetV2 Damage Severity Classifier (93.3% Acc)
├── datasets/                          # Curated datasets (YOLO, disease splits, damage classes)
├── results/                           # Test metrics, confusion matrices, and training curves
├── scripts/                           # Standalone training, evaluation, and CLI tools
└── requirements.txt                   # Project dependencies
```

---

## 3. How to Launch the Full-Stack Application

### Option A: Launch Production FastAPI + React App (Single Command)

```powershell
python -m backend.main
```
Then open `http://127.0.0.1:8000` in your web browser:
- **Live AI Diagnostic Vision:** Upload any arecanut palm, fruit bunch, or snail photo to view bounding boxes, snail counts, disease diagnosis, feeding damage severity, and click **Download PDF Prescription**.
- **ArecaKisan AI Chatbot:** Consult the agronomic advisory chatbot in **English** or **Kannada (ಕನ್ನಡ)** with quick prompt chips.
- **Model Benchmarks & Metrics:** Review real test evaluation metrics and model specifications.
- **Plantation Field Manual:** ICAR/CPCRI reference protocols for Koleroga, Bud Rot, YLD, Ring Spot, and Snail eradication.

### Option B: Frontend Hot-Reload Development (Vite)

```powershell
cd frontend
npm run dev
```
Runs at `http://localhost:5173` with automatic API proxying to port 8000.

### Option C: Legacy Flask Single-File Dashboard

```powershell
python app.py
```
Runs at `http://127.0.0.1:5000`.
- **Damage Annotation Studio Tab:** Open plantation photos, drag a box over leaf feeding damage patches, tag severity (`low_damage`, `moderate_damage`, `severe_damage`), and save with one click to expand your dataset. Click **Run Damage Model Training** to train the damage model right from the browser.
- **Dataset Audit Tab:** View directory counts, duplicate resolution, and annotation guidelines.

---

## 4. CLI Inference Utilities

### Snail Detection and Counting:
```powershell
python scripts/predict_count.py --source "test_images/test.jpg" --conf 0.25
```

### Joint Multi-Task Inference (Snail Detection + Disease Diagnosis):
```powershell
python scripts/predict_all.py --image "datasets/snail/snail dataset/snail in arecanut/Screenshot 2026-11-21 114845.png"
```

### Damage Severity Classifier Training:
```powershell
python scripts/train_damage_classifier.py
```
