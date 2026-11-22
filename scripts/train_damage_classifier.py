import os
import json
import time
import copy
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

ROOT = Path(__file__).resolve().parents[1]
SRC_DATA_DIR = ROOT / "datasets" / "damage_dataset"
SPLIT_DATA_DIR = ROOT / "datasets" / "damage_split"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 8
NUM_EPOCHS = 20
LEARNING_RATE = 0.001
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

EXPECTED_CLASSES = ["no_damage", "low_damage", "moderate_damage", "severe_damage"]

def prepare_splits():
    import random
    import shutil
    random.seed(42)
    
    if SPLIT_DATA_DIR.exists():
        shutil.rmtree(SPLIT_DATA_DIR)

    categories = [d for d in SRC_DATA_DIR.iterdir() if d.is_dir()]
    cat_names = [c.name for c in categories]
    print(f"Found {len(categories)} damage classes in {SRC_DATA_DIR}: {cat_names}")

    # Verify 4-class structure
    for exp_c in EXPECTED_CLASSES:
        c_dir = SRC_DATA_DIR / exp_c
        if not c_dir.exists():
            c_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created missing class folder: {c_dir}")

    # Check image counts per class
    counts = {}
    categories = [SRC_DATA_DIR / c for c in EXPECTED_CLASSES if (SRC_DATA_DIR / c).is_dir()]
    for cat in categories:
        imgs = [p for p in cat.glob("*") if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
        counts[cat.name] = len(imgs)

    print("Current class sample distribution:")
    for c_name, count in counts.items():
        print(f"  - {c_name}: {count} image(s)")

    # Validate that no_damage has genuine samples before retraining
    if counts.get("no_damage", 0) < 3:
        raise ValueError(
            f"Cannot retrain 4-class damage classifier: 'no_damage' class has only {counts.get('no_damage', 0)} image(s).\n"
            f"Minimum 3 genuine labelled samples are required for train/val/test split (recommended 50+).\n"
            f"Please populate 'datasets/damage_dataset/no_damage/' with verified undamaged arecanut plant images.\n"
            f"Do not fabricate synthetic images or duplicate existing data."
        )

    for cat in categories:
        imgs = [p for p in cat.glob("*") if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]
        random.shuffle(imgs)

        total = len(imgs)
        n_train = max(1, int(round(total * 0.70)))
        n_val = max(1, int(round(total * 0.20)))
        n_test = max(1, total - n_train - n_val)

        train_imgs = imgs[:n_train]
        val_imgs = imgs[n_train:n_train + n_val]
        test_imgs = imgs[n_train + n_val:]

        for split, flist in [("train", train_imgs), ("val", val_imgs), ("test", test_imgs)]:
            t_dir = SPLIT_DATA_DIR / split / cat.name
            t_dir.mkdir(parents=True, exist_ok=True)
            for f in flist:
                from PIL import Image
                with Image.open(f) as im:
                    rgb = im.convert("RGB")
                    rgb.save(t_dir / f"{f.stem}.jpg", "JPEG", quality=95)

    print(f"4-class damage split prepared at: {SPLIT_DATA_DIR}")

def train_damage_model():
    print("=" * 70)
    print("SNAIL FEEDING DAMAGE SEVERITY CLASSIFICATION TRAINING")
    print(f"Device: {DEVICE}")
    print("=" * 70)

    # 1. Prepare splits
    prepare_splits()

    # 2. Transforms
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]),
        'test': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]),
    }

    image_datasets = {
        x: datasets.ImageFolder(str(SPLIT_DATA_DIR / x), data_transforms[x])
        for x in ['train', 'val', 'test']
    }

    dataloaders = {
        'train': DataLoader(image_datasets['train'], batch_size=BATCH_SIZE, shuffle=True, num_workers=0),
        'val': DataLoader(image_datasets['val'], batch_size=BATCH_SIZE, shuffle=False, num_workers=0),
        'test': DataLoader(image_datasets['test'], batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    }

    dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val', 'test']}
    class_names = image_datasets['train'].classes
    num_classes = len(class_names)

    print(f"Classes ({num_classes}): {class_names}")
    print(f"Train: {dataset_sizes['train']}, Val: {dataset_sizes['val']}, Test: {dataset_sizes['test']}")

    # 3. Model
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    for param in model.features.parameters():
        param.requires_grad = False
    for layer in model.features[-4:]:
        for param in layer.parameters():
            param.requires_grad = True

    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, num_classes)
    )
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)

    best_val_loss = float('inf')
    best_val_acc = 0.0
    best_model_wts = copy.deepcopy(model.state_dict())
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': [], 'epochs': []}

    for epoch in range(1, NUM_EPOCHS + 1):
        for phase in ['train', 'val']:
            model.train() if phase == 'train' else model.eval()
            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double().item() / dataset_sizes[phase]

            if phase == 'train':
                history['train_loss'].append(epoch_loss)
                history['train_acc'].append(epoch_acc)
                history['epochs'].append(epoch)
            else:
                history['val_loss'].append(epoch_loss)
                history['val_acc'].append(epoch_acc)
                scheduler.step(epoch_loss)
                if epoch_loss < best_val_loss:
                    best_val_loss = epoch_loss
                    best_val_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())

        print(f"Epoch {epoch}/{NUM_EPOCHS}: Train Loss {history['train_loss'][-1]:.4f} (Acc {history['train_acc'][-1]*100:.1f}%), Val Loss {history['val_loss'][-1]:.4f} (Acc {history['val_acc'][-1]*100:.1f}%)")

    # 4. Save best model
    model.load_state_dict(best_model_wts)
    best_weights_path = MODELS_DIR / "snail_damage_best.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'best_val_acc': best_val_acc,
        'best_val_loss': best_val_loss,
        'history': history,
        'num_classes': num_classes
    }, best_weights_path)
    print(f"Saved damage model weights to: {best_weights_path}")

    # 5. Evaluate on Test Set
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for inputs, labels in dataloaders['test']:
            inputs = inputs.to(DEVICE)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    all_preds, all_labels = np.array(all_preds), np.array(all_labels)
    test_acc = np.mean(all_preds == all_labels)
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True, zero_division=0)
    print("\n--- Test Set Evaluation ---")
    print(classification_report(all_labels, all_preds, target_names=class_names, zero_division=0))
    print(f"Damage Test Accuracy: {test_acc*100:.2f}%")

    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Oranges)
    plt.title('Snail Feeding Damage Confusion Matrix')
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha='right')
    plt.yticks(tick_marks, class_names)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "damage_confusion_matrix.png", dpi=200)
    plt.close()

    # Save training curves plot
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history['epochs'], history['train_loss'], 'b-o', label='Train Loss')
    plt.plot(history['epochs'], history['val_loss'], 'r-s', label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Damage Classifier Loss')
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(history['epochs'], [a * 100 for a in history['train_acc']], 'b-o', label='Train Acc')
    plt.plot(history['epochs'], [a * 100 for a in history['val_acc']], 'r-s', label='Val Acc')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title('Damage Classifier Accuracy')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "damage_training_curves.png", dpi=200)
    plt.close()

    metrics = {
        'architecture': 'MobileNetV2 (Transfer Learning)',
        'class_names': class_names,
        'dataset_split': dataset_sizes,
        'best_val_acc': float(best_val_acc),
        'best_val_loss': float(best_val_loss),
        'test_accuracy': float(test_acc),
        'classification_report': report,
        'confusion_matrix': cm.tolist()
    }
    with open(RESULTS_DIR / "damage_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("Saved damage metrics to results/damage_metrics.json")

if __name__ == "__main__":
    train_damage_model()
