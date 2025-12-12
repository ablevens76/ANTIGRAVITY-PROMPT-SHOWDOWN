#!/usr/bin/env python3
"""
AGENT 2: VisionModelTrainer
Fine-tunes MobileNetV3 on RTX 4070 for quantum vs compression figure classification.
Uses synthetic training data since paper figure extraction requires specialized tools.
"""

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

# Configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_DIR = Path(__file__).parent / "models"
EPOCHS = 10
BATCH_SIZE = 16
LEARNING_RATE = 1e-4
NUM_CLASSES = 2  # quantum vs compression
SYNTHETIC_SAMPLES = 200  # Synthetic training samples


class SyntheticQuantumDataset(Dataset):
    """
    Generates synthetic images resembling quantum circuit diagrams vs compression visualizations.
    This is a showcase of GPU training pipeline - real deployment would use extracted figures.
    """

    def __init__(self, num_samples=200, transform=None):
        self.num_samples = num_samples
        self.transform = transform
        self.samples = self._generate_samples()

    def _generate_samples(self):
        """Generate synthetic image-label pairs."""
        samples = []
        for i in range(self.num_samples):
            label = i % NUM_CLASSES  # Alternate quantum (0) and compression (1)
            samples.append((i, label))
        return samples

    def _create_quantum_image(self, seed):
        """Create synthetic quantum circuit-like pattern."""
        np.random.seed(seed)
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255

        # Draw horizontal lines (qubit lines)
        for y in [56, 112, 168]:
            img[y - 1 : y + 1, 20:204, :] = [0, 0, 0]

        # Draw random gates (circles and rectangles)
        for _ in range(8):
            x = np.random.randint(30, 190)
            y = np.random.choice([56, 112, 168])
            size = np.random.randint(10, 20)
            color = [np.random.randint(50, 200) for _ in range(3)]
            img[max(0, y - size) : min(224, y + size), max(0, x - size) : min(224, x + size), :] = (
                color
            )

        return Image.fromarray(img)

    def _create_compression_image(self, seed):
        """Create synthetic compression/wave-like pattern."""
        np.random.seed(seed)
        img = np.zeros((224, 224, 3), dtype=np.uint8)

        # Draw wave patterns
        for y in range(224):
            for x in range(224):
                val = int(127 + 127 * np.sin(x / 10 + seed) * np.cos(y / 15))
                img[y, x, :] = [val, val // 2, 255 - val]

        # Add compression blocks
        for _ in range(4):
            x1 = np.random.randint(0, 180)
            y1 = np.random.randint(0, 180)
            x2 = x1 + np.random.randint(20, 44)
            y2 = y1 + np.random.randint(20, 44)
            brightness = np.random.randint(100, 255)
            img[y1:y2, x1:x2, :] = [brightness, brightness, brightness]

        return Image.fromarray(img)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        seed, label = self.samples[idx]

        if label == 0:  # Quantum
            img = self._create_quantum_image(seed)
        else:  # Compression
            img = self._create_compression_image(seed)

        if self.transform:
            img = self.transform(img)

        return img, label


def create_model():
    """Create MobileNetV3-Small with custom classifier head."""
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)

    # Freeze backbone for faster training
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier
    model.classifier = nn.Sequential(
        nn.Linear(576, 256),
        nn.Hardswish(),
        nn.Dropout(p=0.2),
        nn.Linear(256, NUM_CLASSES),
    )

    return model.to(DEVICE)


def train_model():
    """Train MobileNetV3 on synthetic quantum vs compression dataset."""
    print("=" * 60)
    print("🧠 AGENT 2: VisionModelTrainer - STARTING")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"GPU: {torch.cuda.get_device_name() if torch.cuda.is_available() else 'N/A'}")
    print(f"Epochs: {EPOCHS}")
    print(f"Batch Size: {BATCH_SIZE}")
    print("-" * 60)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Data transforms
    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Create datasets
    train_dataset = SyntheticQuantumDataset(num_samples=SYNTHETIC_SAMPLES, transform=transform)
    val_dataset = SyntheticQuantumDataset(num_samples=50, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # Model, loss, optimizer
    model = create_model()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.classifier.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    # Training loop
    best_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    for epoch in range(EPOCHS):
        # Training phase
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0

        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        train_acc = 100.0 * train_correct / train_total

        # Validation phase
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()

        val_acc = 100.0 * val_correct / val_total
        scheduler.step()

        history["train_loss"].append(train_loss / len(train_loader))
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss / len(val_loader))
        history["val_acc"].append(val_acc)

        print(
            f"  Epoch [{epoch+1:02d}/{EPOCHS}] "
            f"Train Loss: {train_loss/len(train_loader):.4f} | "
            f"Train Acc: {train_acc:.1f}% | "
            f"Val Acc: {val_acc:.1f}%"
        )

        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_acc": val_acc,
                    "history": history,
                },
                MODEL_DIR / "mobilenetv3_quantum.pth",
            )

    print(f"\n💾 Best model saved with {best_acc:.1f}% validation accuracy")

    # Save training history
    with open(MODEL_DIR / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print("\n" + "=" * 60)
    print("🧠 AGENT 2: VisionModelTrainer - COMPLETE")
    print("=" * 60)

    return model, history


def generate_predictions(model):
    """Generate sample predictions on synthetic test images."""
    print("\n📊 Generating sample predictions...")

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    test_dataset = SyntheticQuantumDataset(num_samples=10, transform=transform)
    model.eval()

    predictions = []
    class_names = ["Quantum Circuit", "Compression Visual"]

    with torch.no_grad():
        for i in range(len(test_dataset)):
            img, true_label = test_dataset[i]
            img = img.unsqueeze(0).to(DEVICE)

            output = model(img)
            probs = torch.softmax(output, dim=1)
            pred_label = output.argmax(dim=1).item()
            confidence = probs[0][pred_label].item()

            predictions.append(
                {
                    "sample": i,
                    "true_class": class_names[true_label],
                    "predicted_class": class_names[pred_label],
                    "confidence": f"{confidence*100:.1f}%",
                    "correct": pred_label == true_label,
                }
            )

            status = "✅" if pred_label == true_label else "❌"
            print(
                f"  {status} Sample {i}: True={class_names[true_label]}, "
                f"Pred={class_names[pred_label]} ({confidence*100:.1f}%)"
            )

    # Save predictions
    with open(MODEL_DIR / "sample_predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)

    accuracy = sum(p["correct"] for p in predictions) / len(predictions) * 100
    print(f"\n📈 Test Accuracy: {accuracy:.1f}%")

    return predictions


if __name__ == "__main__":
    model, history = train_model()
    predictions = generate_predictions(model)
