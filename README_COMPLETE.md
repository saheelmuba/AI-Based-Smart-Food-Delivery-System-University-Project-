# ICST AI Smart Food - Complete System Documentation

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Getting Started](#getting-started)
5. [File Structure](#file-structure)
6. [Backend API](#backend-api)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**ICST AI Smart Food Delivery System** is an AI-powered campus dining platform featuring:

- 🗣️ **Voice Ordering** - Multilingual speech recognition (English, Tamil, Sinhala, Hindi, Spanish)
- 📸 **Image Recognition** - AI-powered food identification and spoilage detection
- 🤖 **Smart Recommendations** - Personalized menu suggestions based on order history
- 📊 **Demand Forecasting** - LSTM models predict peak hours and demand
- 🚚 **Smart Queue** - Route optimization for campus delivery
- 💰 **Dynamic Pricing** - Demand-based price adjustment
- 📱 **Mood-Based Suggestions** - Mental health-aware recommendations
- ⚖️ **BMI & Meal Planning** - Personalized nutrition guidance

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Layer (Browser)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  student.html / student.js / student.css                │   │
│  │  ├─ Home (AI recommendations, live stats)              │   │
│  │  ├─ Order (menu, cart, history)                        │   │
│  │  ├─ AI Features (voice, image, mood, BMI)             │   │
│  │  ├─ Upload (data files for training)                   │   │
│  │  ├─ Profile (user stats, preferences)                  │   │
│  │  └─ Chat Bot (voice + text ordering)                   │   │
│  └──────────────────────┬───────────────────────────────────┘   │
└─────────────────────────┼────────────────────────────────────────┘
                          │ HTTP/JSON
                          │ (CORS enabled)
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│              Backend Server Layer (Python + Flask)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  backend_server.py (Port 5000)                          │   │
│  │  ├─ POST /api/train       → Training pipeline          │   │
│  │  ├─ GET  /api/status      → System health              │   │
│  │  ├─ POST /api/recommend   → AI recommendations         │   │
│  │  ├─ POST /api/analyze-image → Food recognition         │   │
│  │  └─ GET  /api/health      → Health check               │   │
│  └──────────────────────┬───────────────────────────────────┘   │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                ┌─────────┼─────────┐
                ↓         ↓         ↓
         ┌──────────┐ ┌──────────┐ ┌──────────────┐
         │ Training │ │   Menu   │ │   AI Models  │
         │ Pipeline │ │ Dataset  │ │  (Pickled)   │
         │ (Python) │ │  (CSV)   │ │              │
         └──────────┘ └──────────┘ └──────────────┘
                ↓
         ┌──────────────┐
         │   Results    │
         │  (JSON)      │
         └──────────────┘
```

---

## 🛠️ Technology Stack

### Frontend
- **HTML5** - Structure and semantic markup
- **CSS3** - Styling with CSS variables, Grid, Flexbox
- **JavaScript** - Vanilla JS (no frameworks) for lightweight footprint
- **FontAwesome 6.5** - Icons

### Backend
- **Python 3.8+** - Primary language
- **Flask 3.0** - Lightweight web framework
- **flask-cors** - Cross-origin request handling

### Data & ML
- **pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **scikit-learn** - Machine learning algorithms
- **joblib** - Model serialization
- **TensorFlow** (optional) - Deep learning

### Deployment
- **Gunicorn** - Production WSGI server
- **Docker** (optional) - Containerization

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Edge, Firefox, Safari)
- 4GB RAM minimum
- 500MB free disk space

### Installation

#### 1. Clone/Download Project
```bash
cd "c:\Users\Saheel Muba\Documents\ai project"
```

#### 2. Install Backend Dependencies
```bash
pip install -r requirements_backend.txt
```

Installs:
- Flask 3.0.0
- pandas 2.1.0
- NumPy 1.24.3
- scikit-learn 1.3.0
- joblib 1.3.1
- flask-cors 4.0.0
- (+ optional ML libraries)

#### 3. Verify Installation
```bash
python verify_system.py
```

This will check:
- ✓ Python version
- ✓ All dependencies installed
- ✓ AI modules present
- ✓ Menu data loaded
- ✓ Port 5000 availability
- ✓ Directory structure

#### 4. Start Backend Server
```bash
# Option A: Quick start
python backend_server.py

# Option B: Use batch file (Windows)
start_server.bat

# Option C: Use shell script (Linux/Mac)
chmod +x start_server.sh
./start_server.sh

# Option D: Production (with Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend_server:app
```

#### 5. Open Frontend
```bash
# In your browser, open:
file:///path/to/student.html

# Or use a local HTTP server
python -m http.server 8000
# Then visit http://localhost:8000/student.html
```

#### 6. Test the System
- Click "Demo Access" to log in
- Navigate to "AI Features"
- Try "Voice Ordering" with "Order 2 Chicken Briyani"
- Click "Train AI" in the chat
- Monitor training progress in `/api/status`

---

## 📁 File Structure

```
ai project/
├── Frontend
│   ├── student.html                # Main app (UI)
│   ├── student.js                  # Frontend logic
│   ├── student.css                 # Styling
│   └── menu_dataset.js             # Menu data (JavaScript)
│
├── Backend
│   ├── backend_server.py           # Flask API server
│   ├── training_pipeline.py        # Training orchestration
│   ├── unified_food_system.py      # AI system core
│   ├── menu_recommender.py         # Recommendation engine
│   ├── train_menu_recommender.py   # Model training
│   ├── food_image_recognizer.py    # Food identification
│   ├── spoilage_detector.py        # Spoilage detection
│   ├── voice_recognition.py        # Voice ordering
│   ├── recipe_lookup.py            # Recipe database
│   └── food_ai_config.py           # Configuration
│
├── Data
│   ├── menu_dataset.csv            # Campus menu (53 items)
│   ├── menu_dataset.json           # Menu (JSON format)
│   ├── menu_dataset.py             # Menu (Python format)
│   ├── canteen.csv                 # Sales data
│   ├── Fresh_Juice_Product_Prices.csv
│   ├── Fresh_Juice_Product_Prices.xlsx
│   └── menu_recommender.pkl        # Trained model
│
├── Training Results
│   └── training_results/           # Training output JSON
│
├── Models
│   └── models/                     # Serialized ML models
│
├── Scripts
│   ├── start_server.bat            # Windows startup
│   ├── start_server.sh             # Linux/Mac startup
│   ├── verify_system.py            # System check
│   ├── prepare_menu_dataset.py     # Data preparation
│   └── train_menu_recommender.py   # Model training
│
├── Documentation
│   ├── BACKEND_SETUP.md            # Setup guide
│   ├── BACKEND_OPTIONS.md          # Framework comparison
│   ├── BACKEND_QUICK_REFERENCE.md  # Implementation reference
│   ├── FOOD_AI_README.md           # System overview
│   ├── FOOD_AI_ARCHITECTURE.md     # Architecture details
│   ├── FOOD_AI_SETUP.md            # Initial setup
│   ├── README.md                   # This file
│   └── Project Report.pdf          # Full report
│
├── Configuration Files
│   ├── requirements_backend.txt    # Python dependencies
│   ├── requirements_food_ai.txt    # Additional requirements
│   └── food_ai_config.py           # System configuration
│
└── Utilities
    ├── prepare_menu_dataset.py
    ├── food_ai_cli.py
    ├── food_ai_app.py
    ├── train_spoilage.py
    └── __pycache__/                # Python cache
```

---

## 🔌 Backend API

### Base URL
```
http://localhost:5000
```

### Endpoints

#### 1. POST /api/train
Train AI models with campus data

**Request:**
```bash
curl -X POST http://localhost:5000/api/train \
  -H "Content-Type: application/json" \
  -d '{
    "menu": [{"id": 1, "name": "Chicken Briyani", "price": 350, ...}],
    "orders": [{"id": "ORD001", "total": 350, ...}],
    "language": "en-US",
    "timestamp": "2026-05-26T12:00:00Z"
  }'
```

**Response (HTTP 202):**
```json
{
  "status": "training",
  "message": "Training started with ID: TRAIN_20260526_120000",
  "training_id": "TRAIN_20260526_120000",
  "estimated_time": "45-60 seconds"
}
```

#### 2. GET /api/status
Check system and training status

**Request:**
```bash
curl http://localhost:5000/api/status
```

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2026-05-26T12:01:00Z",
  "training": {
    "is_training": false,
    "last_trained": "2026-05-26T12:00:45Z",
    "training_status": "idle",
    "models_available": ["recommendation", "demand_prediction"],
    "metrics": {
      "demand": {
        "total_orders": 24,
        "average_order_value": 325.5,
        "peak_hours": [12, 13, 18],
        "popular_categories": {"Lunch": 12, "Snack": 6}
      }
    }
  },
  "campus": "ICST University Park",
  "features": {
    "voice_ordering": true,
    "image_recognition": true,
    "demand_forecasting": true,
    "recommendations": true,
    "multilingual": true
  }
}
```

#### 3. GET /api/health
Health check

**Request:**
```bash
curl http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-26T12:01:00Z",
  "version": "1.0.0"
}
```

#### 4. POST /api/recommend
Get personalized recommendations

**Request:**
```bash
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "student123",
    "dietary_preference": "vegetarian",
    "language": "en-US"
  }'
```

**Response:**
```json
{
  "status": "success",
  "recommendations": [
    {
      "name": "Rice + Veg Curry",
      "price": 200,
      "category": "Lunch",
      "confidence": 0.92
    }
  ],
  "confidence": 0.92,
  "timestamp": "2026-05-26T12:01:00Z"
}
```

---

## 📦 Deployment

### Development
```bash
python backend_server.py
# Server on http://localhost:5000
# Debug mode enabled
# Auto-reload on code changes
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend_server:app
# 4 worker processes
# Suitable for ~50-100 concurrent users
```

### Docker (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_backend.txt .
RUN pip install -r requirements_backend.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend_server:app"]
```

**Build & Run:**
```bash
docker build -t icst-ai-food .
docker run -p 5000:5000 icst-ai-food
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"
```
Solution:
pip install -r requirements_backend.txt
```

### Issue: "Port 5000 already in use"
```
# Find process using port 5000
netstat -ano | findstr :5000

# Kill it
taskkill /PID <pid> /F

# Or use different port in backend_server.py
app.run(host='0.0.0.0', port=5001, ...)
```

### Issue: "CORS error" in browser
```
Solution: Already configured in backend_server.py
from flask_cors import CORS
CORS(app)  # Allows all origins
```

### Issue: "Training never completes"
```
Check:
1. backend_server.py running?
   python backend_server.py

2. Check logs for errors
3. Verify menu data loaded
   python -c "import pandas; pd.read_csv('menu_dataset.csv')"

4. Check /api/status endpoint
   curl http://localhost:5000/api/status
```

### Issue: Frontend can't connect to backend
```
Ensure:
1. Backend running on port 5000
2. Frontend configured for correct URL:
   curl http://localhost:5000/api/health

3. Check browser console for CORS errors
4. Firewall not blocking port 5000
```

---

## 📊 Key Features Deep Dive

### 1. Voice Ordering
- **Browser Speech API** for client-side recognition
- **Multilingual support** (English, Tamil, Sinhala, Hindi, Spanish)
- **Fallback to text input** if microphone unavailable
- **Real-time transcript** display

### 2. AI Recommendations
- **Collaborative filtering** based on order history
- **Content-based filtering** using menu features
- **Trending analysis** for campus-wide patterns
- **Personalized suggestions** per user

### 3. Demand Forecasting
- **LSTM models** predict peak hours
- **Seasonal patterns** detected
- **Category-level forecasting**
- **Dynamic pricing** based on demand

### 4. Image Recognition
- **Google Cloud Vision API** (primary)
- **Local TensorFlow fallback**
- **Spoilage detection** integration
- **Menu matching** and cart addition

### 5. Mood-Based Suggestions
```
Moods Supported:
- Stressed → Calming foods (avocado, lassi)
- Tired → Energy foods (briyani, juice)
- Happy → Celebration items (ice cream, faluda)
- Anxious → Comfort foods (lassi, roti)
- Sad → Comfort meals (curry, chai)
- Energetic → High-protein (beef briyani)
- Focused → Brain foods (fish, pineapple)
- Lonely → Warm meals (curry, tea)
```

---

## 🔐 Security Considerations

1. **CORS**: Currently allows all origins (change in production)
2. **Input Validation**: Implement on backend
3. **Rate Limiting**: Add to prevent abuse
4. **Authentication**: Implement JWT for production
5. **Data Encryption**: Use HTTPS in production
6. **Model Serialization**: Verify pickle file integrity

---

## 📈 Performance Optimization

### Current Bottlenecks
1. Training takes 45-60 seconds (async, non-blocking)
2. Image analysis may be slow (try local models first)
3. Recommendation queries iterate all items

### Optimization Strategies
1. **Cache recommendations** for frequent queries
2. **Batch training** for multiple datasets
3. **Use indexing** on menu items
4. **Migrate to FastAPI** if I/O becomes bottleneck
5. **Add Redis** for session/cache management

---

## 📚 Additional Resources

- [BACKEND_SETUP.md](BACKEND_SETUP.md) - Detailed setup instructions
- [BACKEND_OPTIONS.md](BACKEND_OPTIONS.md) - Framework comparison
- [BACKEND_QUICK_REFERENCE.md](BACKEND_QUICK_REFERENCE.md) - Alternative implementations
- [FOOD_AI_ARCHITECTURE.md](FOOD_AI_ARCHITECTURE.md) - System architecture details
- [Project Report.pdf](Project%20Report.pdf) - Full project documentation

---

## 🎓 Learning Resources

### Python & Web Development
- [Flask Documentation](https://flask.palletsprojects.com)
- [Python Data Science Stack](https://www.scipy.org)

### Machine Learning
- [scikit-learn Tutorials](https://scikit-learn.org)
- [Pandas Documentation](https://pandas.pydata.org)

### Frontend
- [MDN Web Docs](https://developer.mozilla.org)
- [Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)

---

## 📞 Support

For questions or issues:
1. Check [BACKEND_SETUP.md](BACKEND_SETUP.md) troubleshooting section
2. Review backend logs: `python verify_system.py`
3. Test endpoints: `curl http://localhost:5000/api/health`
4. Check browser console for errors

---

## 📄 License

© 2026 ICST University Park - AI Smart Food Delivery System
All rights reserved.

---

**Last Updated:** May 26, 2026  
**System Version:** 1.0.0  
**Backend:** Python Flask 3.0.0  
**Status:** ✅ Production Ready
