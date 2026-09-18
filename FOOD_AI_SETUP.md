# 🚀 AI Food Image Recognition - Quick Setup Guide

Follow this step-by-step guide to set up your complete food recognition system.

---

## Step 1: Install Python Packages

```bash
cd "c:\Users\Saheel Muba\Documents\ai project"
pip install -r requirements_food_ai.txt
```

**Expected packages:**
- opencv-python (image processing)
- torch, torchvision (deep learning)
- tensorflow (optional)
- google-cloud-vision (Google API)
- requests (HTTP requests)
- pandas (data handling)
- flask (web server)
- flask-cors (API support)

⏱️ **Time**: 5-10 minutes (depending on internet speed)

---

## Step 2: Setup Dataset Directories

```bash
python train_spoilage.py setup
```

This creates:
```
food_data/datasets/
├── good_food_images/     ← Add fresh food photos
└── spoilage_images/      ← Add spoiled food photos
```

**What to add:**
- **good_food_images/**: Photos of fresh, edible food
  - Chicken, rice, curry, bread, juice, etc.
  - Various angles, lighting conditions
  - **Minimum**: 20 images
  - **Recommended**: 50+ images

- **spoilage_images/**: Photos of spoiled food
  - Moldy bread, rotten fruit, expired items
  - Visible spoilage signs (color change, mold, slime)
  - **Minimum**: 20 images
  - **Recommended**: 50+ images

---

## Step 3: Configure API Credentials (Optional)

### Option A: Google Cloud Vision API (Recommended)

1. Go to: https://console.cloud.google.com
2. Create a new project
3. Enable "Vision API"
4. Create service account → Download JSON key
5. Create `.env` file in project root:

```env
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\credentials.json
```

### Option B: Edamam Recipe API

1. Sign up: https://www.edamam.com/
2. Get your App ID and App Key
3. Add to `.env` file:

```env
EDAMAM_APP_ID=your-app-id
EDAMAM_API_KEY=your-api-key
```

**Note**: Without APIs, the system uses local fallbacks.

---

## Step 4: Train the Spoilage Detection Model

### Check your dataset first:

```bash
python train_spoilage.py check
```

Expected output:
```
📊 Dataset Statistics:
  Good food images:  35 images
  Spoiled images:    28 images
  Total:             63 images
```

### Train the model:

```bash
python train_spoilage.py train --epochs 50 --batch-size 32
```

**What happens:**
- Model learns to distinguish good vs spoiled food
- Saves trained model to `models/spoilage_detector.pth`
- Shows training progress every epoch

**Time**: 10-30 minutes (depends on dataset size and GPU)

**Hardware notes:**
- ✅ GPU (NVIDIA/CUDA): ~5-10 minutes
- 🟡 Apple Silicon (MPS): ~15-20 minutes
- 🔴 CPU only: ~30-60 minutes

---

## Step 5: Test the System

### Test with a single image:

```bash
python food_ai_cli.py analyze path/to/food.jpg
```

Expected output:
```
📸 Analyzing food image: food.jpg
============================================================

🔍 Step 1: Recognizing food items...
✓ Detected: chicken briyani

🧪 Step 2: Checking for spoilage...
✓ Food appears GOOD (Confidence: 89.2%)

📋 Step 3: Fetching ingredients and recipes...
📖 Recipe: Chicken Briyani
Cooking time: 45 minutes
Servings: 4

🧂 Ingredients needed:
  • 500g chicken
  • 2 cups rice
  • 4 green chilis
  • ... (more ingredients)
```

---

## Step 6: Launch the Web Interface

```bash
python food_ai_app.py
```

Expected output:
```
Starting AI Smart Food Delivery - Web Interface
Open your browser and navigate to: http://localhost:5000
Press Ctrl+C to stop the server
```

### Using the web interface:
1. Open `http://localhost:5000` in your browser
2. Drag & drop a food image or click to upload
3. Click "Analyze Food"
4. See results in real-time

---

## Step 7: Batch Process Multiple Images

```bash
python food_ai_cli.py batch --dir ./food_images --output results.json
```

Creates `results.json` with analysis for all images.

---

## 📊 System Configuration

Edit `food_ai_config.py` to customize:

```python
# Change model type
MODEL_CONFIG['spoilage_detection']['backbone'] = 'resnet50'

# Adjust batch size (for memory issues)
MODEL_CONFIG['spoilage_detection']['batch_size'] = 16

# Change device
MODEL_CONFIG['spoilage_detection']['device'] = 'cuda'  # or 'cpu'

# Add food categories
FOOD_CATEGORIES = {
    'custom_category': ['item1', 'item2', ...]
}
```

---

## 🧪 Advanced Usage

### Train with custom parameters:

```bash
python train_spoilage.py train --epochs 100 --batch-size 16 --lr 0.0001
```

### Test inference on trained model:

```bash
python train_spoilage.py test food_images/test.jpg
```

### Use local model only (no APIs):

```bash
python food_ai_cli.py analyze food.jpg --local --no-ingredients
```

### Process directory with custom output:

```bash
python food_ai_cli.py batch --dir C:\Users\...\images --output analysis_report.json
```

---

## 🔍 Verifying Installation

Run this test script to check everything:

```python
# test_setup.py
from pathlib import Path

print("✓ Checking AI Food Recognition System Setup")
print("=" * 50)

# Check files
files_to_check = [
    'food_ai_config.py',
    'food_image_recognizer.py',
    'spoilage_detector.py',
    'recipe_lookup.py',
    'food_ai_cli.py',
    'food_ai_app.py',
]

for file in files_to_check:
    if Path(file).exists():
        print(f"✓ {file}")
    else:
        print(f"✗ Missing: {file}")

# Check directories
dirs = [
    'models',
    'food_data/datasets/good_food_images',
    'food_data/datasets/spoilage_images',
]

for dir in dirs:
    if Path(dir).exists():
        print(f"✓ {dir}/")
    else:
        print(f"⚠ Create: {dir}/")

# Check imports
try:
    import torch
    print(f"✓ PyTorch {torch.__version__}")
except:
    print("✗ PyTorch not installed")

try:
    import cv2
    print("✓ OpenCV installed")
except:
    print("✗ OpenCV not installed")

print("=" * 50)
print("Setup verification complete!")
```

Run it:
```bash
python test_setup.py
```

---

## ❓ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Solution:**
```bash
pip install torch torchvision
```

### Issue: "CUDA not found" / "GPU not detected"

**Solution:** Use CPU instead
```python
# In food_ai_config.py
MODEL_CONFIG['spoilage_detection']['device'] = 'cpu'
```

### Issue: "API credentials not found"

**Solution:** Create `.env` file with:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/json
EDAMAM_APP_ID=your-id
EDAMAM_API_KEY=your-key
```

### Issue: "No training data found"

**Solution:** Verify directory structure:
```
food_data/datasets/
├── good_food_images/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ... (at least 20)
└── spoilage_images/
    ├── spoiled1.jpg
    ├── spoiled2.jpg
    └── ... (at least 20)
```

### Issue: Training is very slow

**Solution:**
- Reduce batch size: `--batch-size 8`
- Reduce epochs: `--epochs 20`
- Use GPU if available
- Reduce image size in `food_ai_config.py`

### Issue: Out of memory during training

**Solution:**
```bash
python train_spoilage.py train --batch-size 8
```

---

## 🎯 What's Next?

### 1. **Improve the Model**
   - Add more diverse images
   - Retrain with 100+ epochs
   - Use GPU for faster training

### 2. **Deploy to Production**
   - Set up HTTPS
   - Configure proper logging
   - Add database for results
   - Deploy on cloud (Azure, Google Cloud, AWS)

### 3. **Integrate with Chatbot**
   - Connect to `voice_recognition.py`
   - Show food analysis results in chat
   - Add to delivery system

### 4. **Add More Features**
   - Allergen detection
   - Nutritional analysis
   - Dietary recommendations
   - User preference learning

---

## 📞 Quick Reference

```bash
# Training
python train_spoilage.py setup              # Setup directories
python train_spoilage.py check              # Check dataset
python train_spoilage.py train --epochs 50 # Train model
python train_spoilage.py test image.jpg    # Test image

# CLI
python food_ai_cli.py analyze image.jpg            # Single image
python food_ai_cli.py analyze image.jpg --local    # Use local model
python food_ai_cli.py batch --dir ./images         # Batch process
python food_ai_cli.py batch --dir ./images --output results.json

# Web App
python food_ai_app.py                      # Start web server
# Open: http://localhost:5000
```

---

**Setup Complete!** 🎉

Your AI Food Image Recognition System is ready to use.

Start with: `python food_ai_app.py`

Questions? Check `FOOD_AI_README.md` for detailed documentation.
