"""
Configuration for AI Smart Food Delivery System - Image Recognition Module
"""
import os
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'food_data'
MODEL_DIR = ROOT / 'models'
DATASET_DIR = DATA_DIR / 'datasets'
SPOILAGE_DATASET = DATASET_DIR / 'spoilage_images'
GOOD_FOOD_DATASET = DATASET_DIR / 'good_food_images'

# Create directories if they don't exist
MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
DATASET_DIR.mkdir(exist_ok=True)
SPOILAGE_DATASET.mkdir(exist_ok=True)
GOOD_FOOD_DATASET.mkdir(exist_ok=True)

# API Configuration
GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id')
GOOGLE_CLOUD_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')

EDAMAM_APP_ID = os.getenv('EDAMAM_APP_ID', '')
EDAMAM_API_KEY = os.getenv('EDAMAM_API_KEY', '')

# Model Configuration
MODEL_CONFIG = {
    'food_recognition': {
        'backbone': 'resnet50',
        'pretrained': True,
        'num_classes': 101,  # Food-101 dataset
        'input_size': 224,
    },
    'spoilage_detection': {
        'backbone': 'efficientnet_b0',
        'pretrained': True,
        'num_classes': 2,  # Good / Spoiled
        'input_size': 224,
        'batch_size': 32,
        'epochs': 50,
        'learning_rate': 0.001,
        'device': 'cuda',  # or 'cpu'
    }
}

# Food Categories (used when API is unavailable)
FOOD_CATEGORIES = {
    'breakfast': ['chicken rotti', 'egg rotti', 'vegetable rotti', 'noodles', 'bread sambol'],
    'lunch': ['chicken briyani', 'rice and veg curry', 'rice and chicken curry', 'fish curry'],
    'dinner': ['kottu rotti', 'fried rice', 'samosa', 'sandwich'],
    'beverage': ['orange juice', 'mango juice', 'ice cream', 'lassi', 'mojito'],
    'snacks': ['samosa', 'cutlet', 'roll', 'sandwich'],
}

# Spoilage Detection Rules
SPOILAGE_INDICATORS = {
    'color_changes': ['brown_spots', 'dark_discoloration', 'unusual_color'],
    'texture_changes': ['mold', 'sliminess', 'wrinkled_skin', 'dents'],
    'smell_indicators': ['fermented_odor', 'rotten_smell', 'sour_odor'],  # For reference
    'time_based': 'consult_with_api',
}

# Response Languages
SUPPORTED_LANGUAGES = {
    'en-US': 'English',
    'ta-IN': 'Tamil',
    'si-LK': 'Sinhala',
    'hi-IN': 'Hindi',
    'es-ES': 'Spanish',
}

# Confidence Thresholds
CONFIDENCE_THRESHOLDS = {
    'food_recognition': 0.70,      # 70% confidence for food classification
    'spoilage_detection': 0.75,    # 75% confidence for spoilage detection
}

# API Endpoints
ENDPOINTS = {
    'google_vision': 'https://vision.googleapis.com/v1/images:annotate',
    'edamam_recipe': 'https://api.edamam.com/api/recipes/v2',
    'edamam_nutrition': 'https://api.edamam.com/api/nutrition-data/v3/nutrients',
}

# Database (menu items)
MENU_CSV_PATH = ROOT / 'menu_dataset.csv'

# Models file paths
SPOILAGE_MODEL_PATH = MODEL_DIR / 'spoilage_detector.pth'
SPOILAGE_MODEL_LEGACY = MODEL_DIR / 'spoilage_detector.pkl'
FOOD_RECOGNITION_MODEL_PATH = MODEL_DIR / 'food_recognizer.pth'
FOOD_LABELS_PATH = MODEL_DIR / 'food_labels.json'
