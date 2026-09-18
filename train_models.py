"""
Training utilities for Food Recognition and Spoilage Detection
Run: python train_models.py --train_food --train_spoilage

This script will download Food-101 via torchvision (if not present), fine-tune a ResNet50
for the food recognition task, and call the existing `SpoilageDetector.train` method to
train the spoilage detector on local `food_data/datasets` images.
"""
import argparse
import json
from pathlib import Path
import time

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import transforms, datasets, models

from food_ai_config import (
    MODEL_DIR,
    FOOD_RECOGNITION_MODEL_PATH,
    FOOD_LABELS_PATH,
    MODEL_CONFIG,
)
from spoilage_detector import SpoilageDetector


def train_food_recognizer(epochs: int = 3, batch_size: int = 64, lr: float = 1e-4, device: str = 'cuda'):
    print('Preparing Food-101 dataset (this may download ~350MB)')

    transform_train = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])

    transform_val = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
    ])

    data_root = Path('food_data/datasets/food-101')
    data_root.mkdir(parents=True, exist_ok=True)

    train_dataset = datasets.Food101(root=str(data_root), split='train', download=True, transform=transform_train)
    val_dataset = datasets.Food101(root=str(data_root), split='test', download=True, transform=transform_val)

    num_classes = len(train_dataset.classes)
    print(f'Found {num_classes} classes')

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    device = torch.device(device if torch.cuda.is_available() and device == 'cuda' else 'cpu')

    model = models.resnet50(pretrained=True)
    # Replace final layer
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    best_acc = 0.0
    for epoch in range(epochs):
        t0 = time.time()
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        avg_loss = running_loss / len(train_loader)

        # Validation
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (preds == labels).sum().item()

        acc = correct / total if total > 0 else 0
        elapsed = time.time() - t0
        print(f'Epoch {epoch+1}/{epochs} - loss: {avg_loss:.4f} - val_acc: {acc:.4f} - time: {elapsed:.1f}s')

        # Save best
        if acc > best_acc:
            best_acc = acc
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), FOOD_RECOGNITION_MODEL_PATH)
            # Save label mapping
            labels_map = {str(i): c for i, c in enumerate(train_dataset.classes)}
            with open(FOOD_LABELS_PATH, 'w', encoding='utf-8') as fh:
                json.dump(labels_map, fh, ensure_ascii=False, indent=2)
            print(f'Saved best food model (acc={best_acc:.4f}) to {FOOD_RECOGNITION_MODEL_PATH}')

    print('Food training complete')


def train_spoilage_detector(epochs: int = None, batch_size: int = None, lr: float = None, device: str = 'cpu'):
    cfg = MODEL_CONFIG.get('spoilage_detection', {})
    if epochs is None:
        epochs = cfg.get('epochs', 10)
    if batch_size is None:
        batch_size = cfg.get('batch_size', 32)
    if lr is None:
        lr = cfg.get('learning_rate', 0.001)

    print('Starting spoilage detector training...')
    sd = SpoilageDetector(backbone=cfg.get('backbone','efficientnet_b0'), device=device)
    success = sd.train(epochs=epochs, batch_size=batch_size, lr=lr)
    if success:
        print('Spoilage detector training completed and model saved')
    else:
        print('Spoilage detector training failed or no data found')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_food', action='store_true')
    parser.add_argument('--train_spoilage', action='store_true')
    parser.add_argument('--epochs', type=int, default=None)
    parser.add_argument('--batch_size', type=int, default=None)
    parser.add_argument('--device', type=str, default='cuda')
    args = parser.parse_args()

    if not args.train_food and not args.train_spoilage:
        print('Nothing to do. Use --train_food and/or --train_spoilage')

    if args.train_food:
        train_food_recognizer(epochs=args.epochs or 3, batch_size=args.batch_size or 64, device=args.device)

    if args.train_spoilage:
        train_spoilage_detector(epochs=args.epochs, batch_size=args.batch_size, device=args.device)
