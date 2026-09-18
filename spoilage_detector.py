"""
Spoilage Detection Model
Trains and infers whether food is spoiled or good based on images
"""
import os
import pickle
from pathlib import Path
from typing import Tuple, Dict, List
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import cv2

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader, random_split
    from torchvision import transforms, models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    Dataset = object
    DataLoader = object
    random_split = None
    transforms = None
    models = None
    nn = None
    optim = None

from food_ai_config import (
    SPOILAGE_DATASET,
    GOOD_FOOD_DATASET,
    SPOILAGE_MODEL_PATH,
    MODEL_CONFIG,
    CONFIDENCE_THRESHOLDS,
)


class FoodImageDataset(Dataset):
    """PyTorch Dataset for food images (Good vs Spoiled)"""
    
    def __init__(self, image_paths: List[str], labels: List[int], transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image_path = self.image_paths[idx]
        image = Image.open(image_path).convert('RGB')
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


class SpoilageDetector:
    """Deep learning model for food spoilage detection"""
    
    def __init__(self, backbone: str = 'efficientnet_b0', device: str = 'cpu'):
        self.backbone = backbone
        self.device = device
        self.model = None
        self.transform = None
        self.scaler = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model architecture"""
        if not TORCH_AVAILABLE:
            print("PyTorch not available. Install with: pip install torch torchvision")
            return
        
        try:
            if self.backbone == 'efficientnet_b0':
                base_model = models.efficientnet_b0(pretrained=True)
                num_features = base_model.classifier[1].in_features
            elif self.backbone == 'resnet50':
                base_model = models.resnet50(pretrained=True)
                num_features = base_model.fc.in_features
            else:
                raise ValueError(f"Unknown backbone: {self.backbone}")
            
            # Freeze backbone
            for param in base_model.parameters():
                param.requires_grad = False
            
            # Replace classifier
            if self.backbone == 'efficientnet_b0':
                base_model.classifier = nn.Sequential(
                    nn.Dropout(p=0.2),
                    nn.Linear(num_features, 128),
                    nn.ReLU(),
                    nn.Dropout(p=0.2),
                    nn.Linear(128, 2),  # Good/Spoiled
                )
            else:
                base_model.fc = nn.Sequential(
                    nn.Linear(num_features, 128),
                    nn.ReLU(),
                    nn.Dropout(p=0.2),
                    nn.Linear(128, 2),
                )
            
            self.model = base_model.to(self.device)
            
            # Setup transform
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(brightness=0.2, contrast=0.2),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
            
            print(f"Spoilage detector initialized with {self.backbone}")
        
        except Exception as e:
            print(f"Error initializing model: {e}")
    
    def collect_training_data(self) -> Tuple[List[str], List[int]]:
        """Collect image paths and labels from dataset directories"""
        image_paths = []
        labels = []
        
        # Good food images (label = 0)
        good_dir = Path(GOOD_FOOD_DATASET)
        if good_dir.exists():
            for img_path in good_dir.glob('**/*.jpg') + good_dir.glob('**/*.png'):
                image_paths.append(str(img_path))
                labels.append(0)  # Good
        
        # Spoiled food images (label = 1)
        spoilage_dir = Path(SPOILAGE_DATASET)
        if spoilage_dir.exists():
            for img_path in spoilage_dir.glob('**/*.jpg') + spoilage_dir.glob('**/*.png'):
                image_paths.append(str(img_path))
                labels.append(1)  # Spoiled
        
        print(f"Collected {len(image_paths)} training images:")
        print(f"  Good food: {sum(1 for l in labels if l == 0)}")
        print(f"  Spoiled food: {sum(1 for l in labels if l == 1)}")
        
        return image_paths, labels
    
    def train(self, epochs: int = 50, batch_size: int = 32, lr: float = 0.001, 
              val_split: float = 0.2):
        """Train the spoilage detection model"""
        
        if self.model is None or not TORCH_AVAILABLE:
            print("Model not initialized or PyTorch unavailable")
            return False
        
        # Collect data
        image_paths, labels = self.collect_training_data()
        
        if len(image_paths) == 0:
            print(f"No training data found in:")
            print(f"  Good: {GOOD_FOOD_DATASET}")
            print(f"  Spoiled: {SPOILAGE_DATASET}")
            print("Please add images to these directories first.")
            return False
        
        # Split data
        train_paths, val_paths, train_labels, val_labels = train_test_split(
            image_paths, labels, test_size=val_split, random_state=42, stratify=labels
        )
        
        # Create datasets
        train_dataset = FoodImageDataset(train_paths, train_labels, transform=self.transform)
        val_dataset = FoodImageDataset(val_paths, val_labels, transform=self.transform)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        
        # Setup training
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5)
        
        best_val_loss = float('inf')
        
        # Training loop
        for epoch in range(epochs):
            # Train
            self.model.train()
            train_loss = 0.0
            for images, labels_batch in train_loader:
                images = images.to(self.device)
                labels_batch = labels_batch.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(images)
                loss = criterion(outputs, labels_batch)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validate
            self.model.eval()
            val_loss = 0.0
            correct = 0
            total = 0
            with torch.no_grad():
                for images, labels_batch in val_loader:
                    images = images.to(self.device)
                    labels_batch = labels_batch.to(self.device)
                    
                    outputs = self.model(images)
                    loss = criterion(outputs, labels_batch)
                    val_loss += loss.item()
                    
                    _, predicted = torch.max(outputs.data, 1)
                    total += labels_batch.size(0)
                    correct += (predicted == labels_batch).sum().item()
            
            val_accuracy = 100 * correct / total
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            
            print(f"Epoch [{epoch+1}/{epochs}]")
            print(f"  Train Loss: {avg_train_loss:.4f}")
            print(f"  Val Loss: {avg_val_loss:.4f}, Accuracy: {val_accuracy:.2f}%")
            
            scheduler.step(avg_val_loss)
            
            # Save best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                self.save(SPOILAGE_MODEL_PATH)
                print(f"  Model saved to {SPOILAGE_MODEL_PATH}")
        
        return True
    
    def infer(self, image_path: str) -> Dict:
        """Infer spoilage status of a food image"""
        
        if self.model is None or not TORCH_AVAILABLE:
            return {
                'success': False,
                'error': 'Model not initialized',
                'spoiled_probability': None,
                'status': None,
            }
        
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                good_prob = probabilities[0, 0].item()
                spoiled_prob = probabilities[0, 1].item()
                prediction = 1 if spoiled_prob > good_prob else 0
            
            confidence = max(good_prob, spoiled_prob)
            threshold = CONFIDENCE_THRESHOLDS.get('spoilage_detection', 0.75)
            
            return {
                'success': True,
                'status': 'SPOILED' if prediction == 1 else 'GOOD',
                'good_probability': float(good_prob),
                'spoiled_probability': float(spoiled_prob),
                'confidence': float(confidence),
                'meets_threshold': confidence >= threshold,
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'spoiled_probability': None,
                'status': None,
            }
    
    def save(self, path: str):
        """Save model to disk"""
        if self.model is None:
            return False
        
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(self.model.state_dict(), path)
            print(f"Model saved to {path}")
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load(self, path: str):
        """Load model from disk"""
        if self.model is None:
            return False
        
        try:
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            print(f"Model loaded from {path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False


class SimpleSpoilageClassifier:
    """Fallback rule-based spoilage detector using color analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def extract_color_features(self, image_path: str) -> np.ndarray:
        """Extract RGB color histogram features"""
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        features = []
        
        for channel in cv2.split(image):
            hist = cv2.calcHist([channel], [0], None, [16], [0, 256])
            features.extend(hist.flatten())
        
        return np.array(features).flatten()
    
    def infer_simple(self, image_path: str) -> Dict:
        """Simple color-based spoilage detection"""
        try:
            features = self.extract_color_features(image_path)
            if features is None:
                return {'success': False, 'error': 'Could not read image'}
            
            # Heuristic: high dark pixels = possible spoilage
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            dark_ratio = np.sum(gray < 80) / gray.size
            
            spoilage_score = dark_ratio * 100
            threshold = 25
            
            return {
                'success': True,
                'spoilage_score': float(spoilage_score),
                'threshold': threshold,
                'status': 'SPOILED' if spoilage_score > threshold else 'GOOD',
                'confidence': min(0.7, spoilage_score / 100),
                'method': 'color_heuristic',
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
