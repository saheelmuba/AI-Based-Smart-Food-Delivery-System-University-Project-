# Backend Server Setup & Integration Guide

## Overview

The AI Smart Food Delivery System backend provides a complete training pipeline server with the following endpoints:

- **POST /api/train** - Train AI models with menu and order data
- **GET /api/status** - Check system health and training status
- **POST /api/recommend** - Get AI recommendations
- **POST /api/analyze-image** - Analyze food images
- **GET /api/health** - Simple health check

## Prerequisites

### System Requirements
- Python 3.8+
- pip (Python package manager)
- 4GB RAM minimum (8GB recommended)
- ~500MB free disk space

### Installation Steps

#### 1. Install Dependencies

```bash
cd "c:\Users\Saheel Muba\Documents\ai project"
pip install -r requirements_backend.txt
```

This installs:
- Flask 3.0.0 (web framework)
- pandas 2.1.0 (data processing)
- scikit-learn 1.3.0 (ML models)
- joblib 1.3.1 (model serialization)
- PIL, OpenCV (image processing)
- google-cloud-speech (optional, for speech)

#### 2. Verify Installation

```bash
python -c "import flask, pandas, sklearn; print('✓ All core dependencies installed')"
```

#### 3. Test Training Pipeline Import

```bash
python -c "from training_pipeline import CampusDataTrainingPipeline; print('✓ Training pipeline ready')"
```

## Running the Backend Server

### Start the Server

```bash
python backend_server.py
```

Expected output:
```
🚀 Starting ICST AI Smart Food Backend Server...
📍 Campus: ICST University Park
🔗 Training endpoint: POST /api/train
📊 Status endpoint: GET /api/status
🎯 Recommendations: POST /api/recommend
🖼️  Image analysis: POST /api/analyze-image

* Running on http://0.0.0.0:5000
* Debug mode: on
```

The server will be accessible at:
- **Local:** `http://localhost:5000`
- **Network:** `http://<your-ip>:5000`

### Keep Server Running

To keep the server running in the background:

**Windows PowerShell:**
```powershell
$job = Start-Job -ScriptBlock { python backend_server.py }
Write-Host "Server started with Job ID: $($job.Id)"
# Later, stop with: Stop-Job -Id <job-id>
```

**Command Prompt:**
```cmd
start python backend_server.py
```

**For development (recommended):**
```bash
python backend_server.py  # Runs in foreground, easy to see logs
```

## API Endpoint Documentation

### 1. Training Endpoint

**Request:**
```bash
POST /api/train
Content-Type: application/json

{
  "menu": [
    {
      "id": 1,
      "name": "Chicken Briyani",
      "price": 350,
      "category": "Lunch",
      "veg": false,
      "calories": 620,
      "protein": "High Protein"
    }
  ],
  "orders": [
    {
      "id": "ORD001",
      "total": 350,
      "items": ["Chicken Briyani"],
      "timestamp": "2026-05-24T12:00:00"
    }
  ],
  "language": "en-US",
  "timestamp": "2026-05-24T12:15:00"
}
```

**Response (Immediate - Async Training):**
```json
{
  "status": "training",
  "message": "Training started with ID: TRAIN_20260524_121500",
  "training_id": "TRAIN_20260524_121500",
  "estimated_time": "45-60 seconds"
}
```

**Status Response (when training completes):**
```json
{
  "status": "completed",
  "training_id": "TRAIN_20260524_121500",
  "models_trained": ["recommendation", "demand_prediction"],
  "metrics": {
    "demand": {
      "total_orders": 1,
      "average_order_value": 350.0,
      "peak_hours": [12],
      "popular_categories": {"Lunch": 1}
    }
  },
  "message": "Training completed successfully"
}
```

### 2. Status Endpoint

**Request:**
```bash
GET /api/status
```

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2026-05-24T12:16:00",
  "training": {
    "is_training": false,
    "last_trained": "2026-05-24T12:15:30",
    "training_status": "idle",
    "models_available": ["recommendation", "demand_prediction"],
    "metrics": {...}
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

### 3. Recommendations Endpoint

**Request:**
```bash
POST /api/recommend
Content-Type: application/json

{
  "user_id": "student123",
  "dietary_preference": "vegetarian",
  "language": "en-US"
}
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
  "timestamp": "2026-05-24T12:17:00"
}
```

### 4. Health Check

**Request:**
```bash
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-24T12:18:00",
  "version": "1.0.0"
}
```

## Frontend Integration

The frontend (`student.html`/`student.js`) is already configured to send requests to the backend:

### Configuration in student.js

```javascript
const BACKEND_URL = 'http://localhost:5000'; // Change for production

// Called when user clicks "Train AI" in chat
function sendTrainingRequest() {
  const payload = {
    menu: MENU,
    orders: orderHistory,
    language: assistantLanguage,
    timestamp: new Date().toISOString()
  };
  
  return fetch('/api/train', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(res => res.json())
  .then(data => {
    assistantContext.trainingConnected = true;
    return data;
  });
}
```

### Testing the Connection

1. **Start the backend server:**
   ```bash
   python backend_server.py
   ```

2. **Open the frontend:**
   - Open `student.html` in a web browser
   - Navigate to the chat

3. **Test training flow:**
   - Click "Train AI" button in quick replies
   - You should see messages:
     - "Training pipeline request sent..."
     - "Training sync completed successfully" (after ~30 seconds)

## Troubleshooting

### Issue: "Connection refused"

**Cause:** Backend server not running

**Solution:**
```bash
# In terminal, start the server
python backend_server.py

# Verify it's running
curl http://localhost:5000/api/health
```

### Issue: "ModuleNotFoundError: No module named 'training_pipeline'"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements_backend.txt
```

### Issue: "Port 5000 already in use"

**Cause:** Another application is using port 5000

**Solution:**
```bash
# Change port in backend_server.py (line ~450)
# app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)

# Or kill existing process using port 5000
lsof -ti:5000 | xargs kill -9  # Linux/Mac
netstat -ano | findstr :5000   # Windows (find PID)
taskkill /PID <pid> /F         # Windows (kill)
```

### Issue: "CORS error" in browser console

**Cause:** Frontend and backend on different origins

**Solution:** Already handled! `flask-cors` is configured in backend_server.py

```python
from flask_cors import CORS
CORS(app)  # Enables cross-origin requests
```

## Performance Optimization

### For Production Deployment

1. **Use production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 backend_server:app
   ```

2. **Configure for your environment:**
   ```python
   # backend_server.py
   if __name__ == '__main__':
       app.run(
           host='0.0.0.0',
           port=5000,
           debug=False,        # Set to False in production
           threaded=True,
           workers=4           # Increase for concurrent requests
       )
   ```

3. **Add request logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

## Training Metrics & Results

After training completes, check results:

```bash
# View training results
ls training_results/

# Example output
# training_results/TRAIN_20260524_121500.json
```

### Result File Example

```json
{
  "training_id": "TRAIN_20260524_121500",
  "timestamp": "2026-05-24T12:15:30",
  "menu_items_trained": 53,
  "orders_analyzed": 24,
  "language": "en-US",
  "models": [
    "recommendation",
    "demand_prediction"
  ],
  "metrics": {
    "demand": {
      "total_orders": 24,
      "average_order_value": 325.5,
      "peak_hours": [12, 13, 18],
      "popular_categories": {
        "Lunch": 12,
        "Snack": 6,
        "Beverage": 4,
        "Dinner": 2
      }
    }
  },
  "status": "success"
}
```

## Next Steps

1. ✅ **Backend running** → Verify with `curl http://localhost:5000/api/health`
2. ✅ **Frontend connected** → Open `student.html` and test chat
3. ✅ **Training triggered** → Click "Train AI" button
4. ✅ **Results saved** → Check `training_results/` folder

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  student.html / student.js / student.css              │  │
│  │  • Voice ordering                                      │  │
│  │  • Image recognition                                  │  │
│  │  • Chat interface                                     │  │
│  │  • Training trigger button                            │  │
│  └──────────────────┬──────────────────────────────────┘  │
└─────────────────────┼────────────────────────────────────┘
                      │ HTTP/JSON
                      │ POST /api/train
                      │ GET /api/status
                      ↓
┌─────────────────────────────────────────────────────────────┐
│            Backend Server (Flask + Python)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  backend_server.py (Port 5000)                        │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Training Pipeline                              │  │  │
│  │  │ • Load campus menu                             │  │  │
│  │  │ • Process order history                        │  │  │
│  │  │ • Train recommender model                      │  │  │
│  │  │ • Analyze demand patterns                      │  │  │
│  │  │ • Save results to JSON                         │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                      ↓
            ┌──────────────────────┐
            │  training_results/   │
            │  (JSON reports)      │
            └──────────────────────┘
```

## Support

For issues or questions:
1. Check terminal logs for error messages
2. Verify all dependencies are installed
3. Ensure backend port (5000) is not blocked
4. Check browser console for CORS errors
