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
DATA_DIR = ROOT / "datasets" / "arecanut_disease_split"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Hyperparameters
BATCH_SIZE = 16
NUM_EPOCHS = 25
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def get_data_transforms():
    # Mean and std for ImageNet
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]

    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(degrees=15),
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
    return data_transforms

def train_and_evaluate():
    print("=" * 70)
    print("ARECANUT DISEASE CLASSIFICATION TRAINING PIPELINE")
    print(f"Device: {DEVICE}")
    print("=" * 70)

    transforms_dict = get_data_transforms()
    image_datasets = {
        x: datasets.ImageFolder(str(DATA_DIR / x), transforms_dict[x])
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

    print(f"Dataset summary:")
    print(f"  Classes ({num_classes}): {class_names}")
    print(f"  Train samples: {dataset_sizes['train']}")
    print(f"  Val samples:   {dataset_sizes['val']}")
    print(f"  Test samples:  {dataset_sizes['test']}")

    # Transfer Learning: MobileNetV2
    print("\nInitializing Pretrained MobileNetV2 Architecture...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    # Freeze base layers initially
    for param in model.features.parameters():
        param.requires_grad = False

    # Unfreeze top feature blocks for fine-tuning
    for layer in model.features[-4:]:
        for param in layer.parameters():
            param.requires_grad = True

    # Custom classification head
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
    optimizer = optim.AdamW(
        [
            {'params': model.features[-4:].parameters(), 'lr': LEARNING_RATE * 0.1},
            {'params': model.classifier.parameters(), 'lr': LEARNING_RATE}
        ],
        weight_decay=WEIGHT_DECAY
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)

    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_val_loss = float('inf')
    best_val_acc = 0.0

    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': [],
        'epochs': []
    }

    patience = 7
    patience_counter = 0

    print("\nStarting Training & Optimization...")
    for epoch in range(1, NUM_EPOCHS + 1):
        epoch_start = time.time()
        print(f"\nEpoch {epoch}/{NUM_EPOCHS}")
        print("-" * 30)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(DEVICE)
                labels = labels.to(DEVICE)
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

            print(f"{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc * 100:.2f}%")

            # Checkpoint best validation model
            if phase == 'val':
                if epoch_loss < best_val_loss:
                    best_val_loss = epoch_loss
                    best_val_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())
                    patience_counter = 0
                    print(f"  [+] Validation loss improved to {best_val_loss:.4f}! Best model weights updated.")
                else:
                    patience_counter += 1
                    print(f"  [-] Validation loss did not improve ({patience_counter}/{patience})")

        epoch_time = time.time() - epoch_start
        print(f"Epoch {epoch} completed in {epoch_time:.1f}s")

        if patience_counter >= patience:
            print(f"\n[!] Early stopping triggered at epoch {epoch}")
            break

    total_time = time.time() - since
    print(f"\nTraining completed in {total_time // 60:.0f}m {total_time % 60:.0f}s")
    print(f"Best Validation Loss: {best_val_loss:.4f}, Best Validation Acc: {best_val_acc * 100:.2f}%")

    # Load best model weights
    model.load_state_dict(best_model_wts)
    best_weights_path = MODELS_DIR / "arecanut_disease_best.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'best_val_acc': best_val_acc,
        'best_val_loss': best_val_loss,
        'history': history,
        'num_classes': num_classes
    }, best_weights_path)
    print(f"Saved best model checkpoint to: {best_weights_path}")

    # Plot training and validation curves
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history['epochs'], history['train_loss'], 'b-o', label='Train Loss')
    plt.plot(history['epochs'], history['val_loss'], 'r-s', label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (CrossEntropy)')
    plt.title('Training & Validation Loss')
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(history['epochs'], [a * 100 for a in history['train_acc']], 'b-o', label='Train Acc')
    plt.plot(history['epochs'], [a * 100 for a in history['val_acc']], 'r-s', label='Val Acc')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title('Training & Validation Accuracy')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plot_path = RESULTS_DIR / "disease_training_curves.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved learning curves to: {plot_path}")

    # Evaluate on Held-out Test Set
    print("\n" + "=" * 70)
    print("EVALUATION ON UNSEEN HELD-OUT TEST DATASET")
    print("=" * 70)
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

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    test_acc = np.mean(all_preds == all_labels)
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    report_text = classification_report(all_labels, all_preds, target_names=class_names)
    print(report_text)
    print(f"Overall Test Accuracy: {test_acc * 100:.2f}%")

    cm = confusion_matrix(all_labels, all_preds)

    # Plot confusion matrix
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Arecanut Disease Test Set Confusion Matrix')
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha='right')
    plt.yticks(tick_marks, class_names)

    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('Actual True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    cm_plot_path = RESULTS_DIR / "disease_confusion_matrix.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot to: {cm_plot_path}")

    # Save metrics JSON
    metrics = {
        'architecture': 'MobileNetV2 (Pretrained + Fine-Tuned)',
        'class_names': class_names,
        'dataset_split': dataset_sizes,
        'best_val_loss': float(best_val_loss),
        'best_val_acc': float(best_val_acc),
        'test_accuracy': float(test_acc),
        'classification_report': report,
        'confusion_matrix': cm.tolist(),
        'hyperparameters': {
            'epochs_run': len(history['epochs']),
            'batch_size': BATCH_SIZE,
            'learning_rate': LEARNING_RATE,
            'weight_decay': WEIGHT_DECAY,
            'patience': patience
        }
    }
    metrics_path = RESULTS_DIR / "disease_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved evaluation metrics to: {metrics_path}")

if __name__ == "__main__":
    train_and_evaluate()
