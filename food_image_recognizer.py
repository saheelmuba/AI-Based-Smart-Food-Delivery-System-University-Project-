"""
Food Image Recognition Module
Integrates Google Cloud Vision API + Local Models
"""
import base64
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from PIL import Image
import requests

try:
    from google.cloud import vision
    from google.oauth2 import service_account
except ImportError:
    vision = None
    service_account = None

from food_ai_config import (
    GOOGLE_CLOUD_PROJECT_ID,
    GOOGLE_CLOUD_CREDENTIALS,
    CONFIDENCE_THRESHOLDS,
    FOOD_CATEGORIES,
    SUPPORTED_LANGUAGES,
    FOOD_RECOGNITION_MODEL_PATH,
    FOOD_LABELS_PATH,
)


class GoogleVisionFoodRecognizer:
    """Recognize food items using Google Cloud Vision API"""
    
    def __init__(self):
        self.project_id = GOOGLE_CLOUD_PROJECT_ID
        self.credentials_path = GOOGLE_CLOUD_CREDENTIALS
        self.client = None
        self.initialized = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Vision API client"""
        if vision is None:
            print("Warning: google-cloud-vision not installed. Install with: pip install google-cloud-vision")
            return
        
        try:
            if self.credentials_path and Path(self.credentials_path).exists():
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
            else:
                self.client = vision.ImageAnnotatorClient()
            self.initialized = True
            print("Google Vision API client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Google Vision API: {e}")
            print("You can set GOOGLE_APPLICATION_CREDENTIALS env var or pass credentials path")
    
    def _load_image(self, image_path: str) -> bytes:
        """Load image file as bytes"""
        with open(image_path, 'rb') as f:
            return f.read()
    
    def _load_image_from_url(self, url: str) -> bytes:
        """Load image from URL"""
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    
    def recognize_food(self, image_path: Optional[str] = None, 
                      image_url: Optional[str] = None,
                      image_bytes: Optional[bytes] = None) -> Dict:
        """
        Recognize food items in an image using Google Cloud Vision API
        
        Args:
            image_path: Path to local image file
            image_url: URL to image
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with food labels and confidence scores
        """
        if not self.initialized:
            return self._fallback_recognition(image_path, image_url, image_bytes)
        
        try:
            if image_path:
                content = self._load_image(image_path)
            elif image_url:
                content = self._load_image_from_url(image_url)
            elif image_bytes:
                content = image_bytes
            else:
                raise ValueError("Must provide image_path, image_url, or image_bytes")
            
            image = vision.Image(content=content)
            response = self.client.label_detection(image=image)
            
            labels = response.label_annotations
            results = {
                'food_items': [],
                'raw_labels': [],
                'confidence': {},
                'api_used': 'google_vision',
            }
            
            # Extract food-related labels
            for label in labels:
                results['raw_labels'].append({
                    'description': label.description,
                    'confidence': float(label.confidence),
                })
                
                # Filter for food-related labels
                if self._is_food_label(label.description):
                    results['food_items'].append(label.description)
                    results['confidence'][label.description] = float(label.confidence)
            
            results['success'] = True
            return results
            
        except Exception as e:
            print(f"Google Vision API error: {e}")
            return self._fallback_recognition(image_path, image_url, image_bytes)
    
    def _is_food_label(self, label: str) -> bool:
        """Check if label is food-related"""
        food_keywords = [
            'food', 'dish', 'meal', 'breakfast', 'lunch', 'dinner',
            'rice', 'curry', 'bread', 'roti', 'juice', 'drink',
            'meat', 'chicken', 'beef', 'fish', 'egg', 'vegetable',
            'fruit', 'snack', 'dessert', 'beverage', 'pizza', 'burger'
        ]
        return any(keyword in label.lower() for keyword in food_keywords)
    
    def _fallback_recognition(self, image_path, image_url, image_bytes):
        """Fallback recognition using basic image analysis"""
        return {
            'food_items': [],
            'raw_labels': [],
            'confidence': {},
            'api_used': 'fallback_cv',
            'success': False,
            'error': 'Google Vision API not available. Please configure API credentials.',
            'suggestion': 'Check GOOGLE_APPLICATION_CREDENTIALS environment variable'
        }


class LocalFoodRecognizer:
    """Local food recognition using pre-trained models"""
    
    def __init__(self, model_type: str = 'resnet50'):
        self.model_type = model_type
        self.model = None
        self.transform = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize local model"""
        try:
            import torch
            from torchvision import models, transforms
            
            if self.model_type == 'resnet50':
                self.model = models.resnet50(pretrained=True)
                # replace final layer to match fine-tuned model if available
                num_features = self.model.fc.in_features
                self.model.fc = torch.nn.Linear(num_features, 1000)
                self.model.eval()
            elif self.model_type == 'efficientnet':
                self.model = models.efficientnet_b0(pretrained=True)
                self.model.eval()
            else:
                raise ValueError(f"Unknown model: {self.model_type}")
            
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
            # Try to load a fine-tuned food recognition model if available
            try:
                import torch
                import json
                if FOOD_RECOGNITION_MODEL_PATH and Path(FOOD_RECOGNITION_MODEL_PATH).exists():
                    state = torch.load(str(FOOD_RECOGNITION_MODEL_PATH), map_location='cpu')
                    # Attempt to load into model. If shapes mismatch, skip.
                    try:
                        self.model.load_state_dict(state)
                        print(f"Loaded fine-tuned food model from {FOOD_RECOGNITION_MODEL_PATH}")
                    except Exception:
                        print("Found food model file but failed to load state dict (shape mismatch). Using ImageNet backbone.")

                # Load label mapping if present
                if FOOD_LABELS_PATH and Path(FOOD_LABELS_PATH).exists():
                    try:
                        with open(FOOD_LABELS_PATH, 'r', encoding='utf-8') as fh:
                            self.labels = json.load(fh)
                    except Exception:
                        self.labels = None

            except Exception:
                pass

            print(f"Local {self.model_type} model ready")
        except Exception as e:
            print(f"Failed to initialize local model: {e}")
    
    def recognize(self, image_path: str) -> Dict:
        """Recognize food using local pre-trained model"""
        if self.model is None:
            return {
                'success': False,
                'error': 'PyTorch/TorchVision not available',
                'food_items': []
            }
        
        try:
            import torch
            from torch.nn import functional as F

            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0)

            device = next(self.model.parameters()).device
            image_tensor = image_tensor.to(device)

            self.model.eval()
            with torch.no_grad():
                outputs = self.model(image_tensor)

            # If model returns logits, apply softmax
            try:
                probs = F.softmax(outputs, dim=1).cpu().numpy()[0]
            except Exception:
                # If single-dim output or unexpected, return raw string
                return {
                    'success': True,
                    'api_used': 'local_pytorch',
                    'raw_output': str(outputs),
                }

            # Map top predictions to labels if available
            top_idx = probs.argsort()[::-1][:5]
            items = []
            for idx in top_idx:
                label = None
                if self.labels:
                    label = self.labels.get(str(int(idx))) or self.labels.get(str(idx))
                if not label:
                    label = f'class_{idx}'
                items.append({'label': label, 'confidence': float(probs[idx])})

            return {
                'success': True,
                'api_used': 'local_pytorch',
                'food_items': [it['label'] for it in items],
                'confidence': {it['label']: it['confidence'] for it in items},
                'top_predictions': items,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'food_items': []
            }


def recognize_food_hybrid(image_path: str, use_local: bool = False) -> Dict:
    """
    Hybrid approach: try Google Vision API first, fallback to local model
    
    Args:
        image_path: Path to food image
        use_local: Force use of local model
        
    Returns:
        Combined results from available recognizers
    """
    results = {
        'primary': None,
        'fallback': None,
        'merged': {
            'food_items': [],
            'all_apis_used': [],
        }
    }
    
    if not use_local:
        google_recognizer = GoogleVisionFoodRecognizer()
        results['primary'] = google_recognizer.recognize_food(image_path=image_path)
        results['merged']['all_apis_used'].append(results['primary'].get('api_used', 'unknown'))
        if results['primary'].get('success'):
            results['merged']['food_items'] = results['primary'].get('food_items', [])
    
    if not results['primary'] or not results['primary'].get('success'):
        local_recognizer = LocalFoodRecognizer()
        results['fallback'] = local_recognizer.recognize(image_path)
        results['merged']['all_apis_used'].append(results['fallback'].get('api_used', 'unknown'))
        if results['fallback'].get('success'):
            results['merged']['food_items'] = results['fallback'].get('food_items', [])
    
    return results
