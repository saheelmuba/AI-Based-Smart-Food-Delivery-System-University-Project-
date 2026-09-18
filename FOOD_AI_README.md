# 🍛 AI Smart Food Delivery - Image Recognition System

Complete AI solution for food image recognition, spoilage detection, and recipe/ingredient lookup with multilingual support.

---

## 🎯 Features

✅ **Food Image Recognition**
- Google Cloud Vision API integration
- Local PyTorch model fallback
- Hybrid approach with automatic fallback

✅ **Spoilage Detection**
- Deep learning model (EfficientNet B0)
- Trainable with your own food images
- Confidence scoring with visual indicators

✅ **Recipe & Ingredient Lookup**
- Edamam Recipe API integration
- Automatic ingredient extraction
- Nutrition information

✅ **Multilingual Support**
- English, Tamil, Sinhala, Hindi, Spanish
- Automatic response translation
- Language detection

✅ **Multiple Interfaces**
- Web interface (Flask app)
- Command-line interface (CLI)
- Python API

---

## 📋 Project Structure

```
ai project/
├── food_ai_config.py              # Configuration and constants
├── food_image_recognizer.py       # Food recognition module
├── spoilage_detector.py           # Spoilage detection model
├── recipe_lookup.py               # Recipe & ingredient lookup
├── food_ai_cli.py                 # Command-line interface
├── food_ai_app.py                 # Flask web application
├── train_spoilage.py              # Training script
├── requirements_food_ai.txt       # Python dependencies
├── models/                        # Trained models directory
│   └── spoilage_detector.pth     # Trained spoilage model
├── food_data/                     # Food data directory
│   └── datasets/
│       ├── good_food_images/      # Good food training images
│       └── spoilage_images/       # Spoiled food training images
└── uploads/                       # Temporary image uploads
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_food_ai.txt
```

### 2. Setup Dataset Directories

```bash
python train_spoilage.py setup
```

Create subdirectories:
- `food_data/datasets/good_food_images/` → Add photos of fresh, good food
- `food_data/datasets/spoilage_images/` → Add photos of spoiled food

### 3. Train Spoilage Detection Model

```bash
# Check dataset status
python train_spoilage.py check

# Train model (requires GPU recommended)
python train_spoilage.py train --epochs 50 --batch-size 32
```

### 4. Configure API Credentials

Create a `.env` file in the project root:

```env
# Google Cloud Vision API
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Edamam Recipe API (get from https://www.edamam.com/)
EDAMAM_APP_ID=your-app-id
EDAMAM_API_KEY=your-api-key
```

### 5. Run the Web Interface

```bash
python food_ai_app.py
```

Open browser: `http://localhost:5000`

---

## 💻 Usage Examples

### Command-Line Interface

```bash
# Analyze single image
python food_ai_cli.py analyze food.jpg

# Analyze with local model
python food_ai_cli.py analyze food.jpg --local

# Analyze without ingredient lookup
python food_ai_cli.py analyze food.jpg --no-ingredients

# Train model
python food_ai_cli.py train --epochs 100

# Batch process directory
python food_ai_cli.py batch --dir ./food_images --output results.json
```

### Python API

```python
from food_image_recognizer import recognize_food_hybrid
from spoilage_detector import SpoilageDetector
from recipe_lookup import RecipeLookup

# Recognize food
results = recognize_food_hybrid('food.jpg')
print(results['merged']['food_items'])

# Check spoilage
detector = SpoilageDetector()
detector.load('models/spoilage_detector.pth')
spoilage_result = detector.infer('food.jpg')
print(f"Status: {spoilage_result['status']}")

# Get recipe
recipe = RecipeLookup()
ingredients = recipe.get_ingredients_for_food('chicken briyani')
print(ingredients['ingredients'])
```

---

## 🔧 Configuration Guide

### food_ai_config.py

All configuration is centralized:

```python
# Model settings
MODEL_CONFIG['spoilage_detection'] = {
    'backbone': 'efficientnet_b0',
    'epochs': 50,
    'batch_size': 32,
    'learning_rate': 0.001,
    'device': 'cuda',  # or 'cpu'
}

# API endpoints
ENDPOINTS = {
    'google_vision': 'https://vision.googleapis.com/v1/images:annotate',
    'edamam_recipe': 'https://api.edamam.com/api/recipes/v2',
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'food_recognition': 0.70,
    'spoilage_detection': 0.75,
}
```

---

## 🏋️ Training the Model

### Step 1: Prepare Dataset

Create two directories and populate with images:

```
food_data/datasets/
├── good_food_images/
│   ├── fresh_chicken.jpg
│   ├── fresh_rice.jpg
│   └── ... (at least 20 images)
└── spoilage_images/
    ├── spoiled_chicken.jpg
    ├── moldy_bread.jpg
    └── ... (at least 20 images)
```

### Step 2: Check Dataset

```bash
python train_spoilage.py check
```

Output:
```
📊 Dataset Statistics:
  Good food images:  45 images
  Spoiled images:    38 images
  Total:             83 images
```

### Step 3: Train Model

```bash
python train_spoilage.py train --epochs 50 --batch-size 32 --lr 0.001
```

Monitor training progress:
```
Epoch [1/50]
  Train Loss: 0.6789, Val Loss: 0.5432, Accuracy: 78.5%
  Model saved to models/spoilage_detector.pth
...
```

### Step 4: Test the Model

```bash
python train_spoilage.py test food_images/test_image.jpg
```

---

## 🔑 API Configuration

### Google Cloud Vision API

1. Create a project on [Google Cloud Console](https://console.cloud.google.com)
2. Enable Vision API
3. Create service account and download JSON key
4. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Edamam Recipe API

1. Sign up at https://www.edamam.com/
2. Get `App ID` and `App Key`
3. Add to `.env` file:

```env
EDAMAM_APP_ID=abc123
EDAMAM_API_KEY=xyz789
```

---

## 🌐 Web Interface Features

1. **Drag & Drop Upload** - Easy image upload
2. **Real-time Analysis** - Food recognition, spoilage detection
3. **Recipe Display** - Ingredients and cooking time
4. **Responsive Design** - Works on desktop and mobile
5. **Visual Feedback** - Color-coded results (good/warning/danger)

### API Endpoints

```
GET  /                    → Web interface
POST /api/analyze         → Analyze food image
GET  /api/health         → Health check
```

---

## ⚙️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Web Interface (food_ai_app.py)               │
├─────────────────────────────────────────────────────────┤
│  Food Recognition    │  Spoilage Detection  │  Recipes  │
├─────────────────────────────────────────────────────────┤
│  Google Vision API   │  PyTorch Model       │  Edamam   │
├─────────────────────────────────────────────────────────┤
│  Menu Dataset CSV    │  Configuration       │  Cache    │
└─────────────────────────────────────────────────────────┘
```

---

## 🎓 Model Information

### Food Recognition
- **API**: Google Cloud Vision (primary)
- **Fallback**: ResNet50 (PyTorch)
- **Input**: Any image format
- **Output**: Food labels with confidence scores

### Spoilage Detection
- **Model**: EfficientNet B0
- **Framework**: PyTorch
- **Input Size**: 224×224 pixels
- **Output**: Good/Spoiled (binary classification)
- **Accuracy**: ~85-90% (depends on training data)

### Recipe Lookup
- **API**: Edamam Recipe API
- **Fallback**: Local menu database (menu_dataset.csv)
- **Info**: Ingredients, nutrition, cooking time

---

## 📊 Performance Tips

### For Better Food Recognition
- Use clear, well-lit images
- Ensure food is fully visible
- Avoid reflections and shadows
- Use higher resolution images (1080p+)

### For Better Spoilage Detection
- Train with diverse food images
- Include various lighting conditions
- Add images of different spoilage stages
- Use 50+ images per class for best results

### Speed Optimization
- Use GPU for faster inference: `device='cuda'`
- Batch process multiple images
- Cache API responses
- Pre-load models at startup

---

## 🐛 Troubleshooting

### "Google Vision API not available"
```bash
# Solution: Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### "No trained model found"
```bash
# Solution: Train the model first
python train_spoilage.py train
```

### "Edamam API credentials not configured"
```bash
# Solution: Add to .env file
EDAMAM_APP_ID=your-id
EDAMAM_API_KEY=your-key
```

### "CUDA out of memory"
```python
# Solution: Reduce batch size in food_ai_config.py
MODEL_CONFIG['spoilage_detection']['batch_size'] = 16
```

### "Module not found errors"
```bash
# Solution: Reinstall requirements
pip install --upgrade -r requirements_food_ai.txt
```

---

## 🔐 Security Considerations

✓ Uploaded images are deleted after analysis
✓ API credentials stored in `.env` (never in code)
✓ HTTPS recommended for production
✓ CORS enabled for cross-origin requests
✓ Input validation on all endpoints

---

## 📈 Future Enhancements

- [ ] Mobile app (React Native)
- [ ] Real-time camera feed analysis
- [ ] Allergen detection
- [ ] Dietary recommendation engine
- [ ] User preference learning
- [ ] Inventory management
- [ ] Multi-language recipes
- [ ] Integration with food delivery APIs

---

## 📚 References

- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [Edamam API Documentation](https://developer.edamam.com/)
- [PyTorch Documentation](https://pytorch.org/)
- [EfficientNet Paper](https://arxiv.org/abs/1905.11946)

---

## 📝 License

This project is part of the AI Smart Food Delivery System.

---

## 🤝 Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review configuration files
3. Check API credentials
4. Review error logs

---

**Last Updated**: May 24, 2026
**Version**: 1.0.0
