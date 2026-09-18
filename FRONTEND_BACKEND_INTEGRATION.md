# Frontend-Backend Integration Guide

## Quick Start (3 Steps)

### Step 1: Start Backend Server
```bash
python backend_server.py
```

Expected output:
```
🚀 Backend server running on http://0.0.0.0:5000
* Running on http://127.0.0.1:5000
* Debug mode: on
```

### Step 2: Verify Connection
```bash
python test_connection.py
```

This will verify:
- ✓ Backend is running
- ✓ CORS is configured
- ✓ All API endpoints work
- ✓ Frontend files are ready

### Step 3: Open Frontend
Open `student.html` in your browser:
```
File → Open File → student.html
```

Or use a local server:
```bash
python -m http.server 8000
# Then visit: http://localhost:8000/student.html
```

---

## How Frontend Calls Backend

### Request Flow

```
User clicks "Train AI" button
         ↓
Frontend JavaScript calls sendTrainingRequest()
         ↓
fetch() sends POST to http://localhost:5000/api/train
         ↓
Backend receives request, returns 202 Accepted
         ↓
Frontend adds message to chat: "Training started"
         ↓
Backend processes in background thread
         ↓
Frontend periodically checks /api/status
         ↓
Training complete → Chat displays results
```

### Key Functions in Frontend

**student.js** has these connection functions:

```javascript
// 1. Send training request to backend
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
    .then(data => { assistantContext.trainingConnected = true; return data; });
}

// 2. Sync with backend training API
function syncDatasetWithTrainingAPI() {
  sendTrainingRequest()
    .then(data => {
      addChatMsg('bot', translateText('trainingComplete'));
      console.debug('Training sync response', data);
    })
    .catch(err => {
      addChatMsg('bot', translateText('trainingFailed'));
      console.warn('Training sync failed', err);
    });
}

// 3. Trigger training from chat
function askTraining() {
  addChatMsg('user', 'Train AI with dataset');
  const message = translateText('trainingStarted');
  addChatMsg('bot', message);
  syncDatasetWithTrainingAPI();
}
```

---

## Backend API Endpoints

All endpoints are at: `http://localhost:5000`

### 1. POST /api/train
Train AI models with campus data

**Request:**
```javascript
fetch('/api/train', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    menu: [{id, name, price, category, ...}],
    orders: [{id, total, items, ...}],
    language: 'en-US',
    timestamp: '2026-05-26T12:00:00Z'
  })
})
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

### 2. GET /api/status
Check training status

**Request:**
```javascript
fetch('/api/status')
```

**Response (HTTP 200):**
```json
{
  "status": "operational",
  "timestamp": "2026-05-26T12:01:00Z",
  "training": {
    "is_training": false,
    "last_trained": "2026-05-26T12:00:45Z",
    "training_status": "idle",
    "models_available": ["recommendation", "demand_prediction"],
    "metrics": { ... }
  }
}
```

### 3. GET /api/health
Health check

**Request:**
```javascript
fetch('/api/health')
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-26T12:01:00Z",
  "version": "1.0.0"
}
```

### 4. POST /api/recommend
Get recommendations

**Request:**
```javascript
fetch('/api/recommend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: "student123",
    dietary_preference: "vegetarian",
    language: "en-US"
  })
})
```

**Response:**
```json
{
  "status": "success",
  "recommendations": [
    { "name": "Chicken Briyani", "price": 350, "confidence": 0.92 }
  ],
  "confidence": 0.92
}
```

---

## File Connections

### Frontend Files
- **student.html** - Main UI, loads JavaScript
- **student.js** - Contains fetch() calls to backend
- **student.css** - Styling (no backend calls)
- **menu_dataset.js** - Menu data (local, loaded in browser)

### Backend Files
- **backend_server.py** - Flask app with all /api/* routes
- **training_pipeline.py** - Trains ML models
- **menu_recommender.py** - Recommendation engine
- **unified_food_system.py** - Core AI system
- **food_ai_config.py** - Configuration

### Connection Points
```
student.js
  ├─ sendTrainingRequest() 
  │   └─ POST /api/train (backend_server.py)
  ├─ getStatus()
  │   └─ GET /api/status (backend_server.py)
  ├─ askTraining()
  │   └─ syncDatasetWithTrainingAPI() → sends to /api/train
  └─ Chat integration
      └─ Displays training status
```

---

## Testing Endpoints with curl

### Test 1: Health Check
```bash
curl http://localhost:5000/api/health
```

### Test 2: Get Status
```bash
curl http://localhost:5000/api/status
```

### Test 3: Send Training Request
```bash
curl -X POST http://localhost:5000/api/train \
  -H "Content-Type: application/json" \
  -d '{
    "menu": [{"id": 1, "name": "Test", "price": 100}],
    "orders": [],
    "language": "en-US",
    "timestamp": "2026-05-26T12:00:00Z"
  }'
```

### Test 4: Get Recommendations
```bash
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "dietary_preference": "all",
    "language": "en-US"
  }'
```

---

## Troubleshooting

### Issue 1: "Network Error" or "Failed to fetch"
**Solution:**
1. Backend not running:
   ```bash
   python backend_server.py
   ```
2. Check backend is on correct port:
   ```bash
   curl http://localhost:5000/api/health
   ```
3. Frontend served from wrong protocol:
   - Use `file:///` for local HTML
   - Or use `http://localhost:8000` with Python server

### Issue 2: "CORS error" in browser console
**Solution:**
- Backend should have CORS enabled (already configured in backend_server.py)
- Check browser console: Ctrl+Shift+J (Chrome) or F12
- Error should show: "Access to XMLHttpRequest blocked by CORS policy"
- This means backend isn't running or CORS not configured

### Issue 3: Training never completes
**Solution:**
1. Check backend console for errors
2. Check /api/status endpoint returns training_status
3. Check backend logs in terminal
4. Verify menu_dataset.csv exists

### Issue 4: Frontend files not loading styles
**Solution:**
1. Make sure student.css exists
2. Browser may cache old files:
   - Clear cache: Ctrl+Shift+Delete
   - Force reload: Ctrl+Shift+R

### Issue 5: Chat shows "Training sync failed"
**Solution:**
1. Check browser console (F12) for error details
2. Verify backend is running:
   ```bash
   python verify_system.py
   ```
3. Test endpoint directly:
   ```bash
   curl -X POST http://localhost:5000/api/train \
     -H "Content-Type: application/json" \
     -d '{"menu": [], "orders": [], "language": "en-US", "timestamp": ""}'
   ```

---

## Configuration

### Change Backend Port
**In backend_server.py:**
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
```

**In student.js (if needed):**
```javascript
// Add this at top of student.js
const BACKEND_URL = 'http://localhost:5001'; // Change port here

// Then use it in fetch:
fetch(BACKEND_URL + '/api/train', { ... })
```

### Change Frontend Language
- Select language in chat interface dropdown
- Currently supported:
  - English (en-US)
  - Tamil (ta-IN)
  - Sinhala (si-LK)
  - Hindi (hi-IN)
  - Spanish (es-ES)

---

## Monitoring Training

### Via Browser
1. Open student.html
2. Click "Train AI" button
3. Chat will show status messages

### Via Terminal
```bash
# Check status
curl http://localhost:5000/api/status | python -m json.tool

# Watch status every 2 seconds (Linux/Mac)
watch -n 2 "curl -s http://localhost:5000/api/status | python -m json.tool"
```

### Via Python
```python
import requests
import json
import time

for i in range(10):
    resp = requests.get('http://localhost:5000/api/status')
    data = resp.json()
    print(f"Training: {data['training']['is_training']}")
    print(f"Status: {data['training']['training_status']}")
    time.sleep(2)
```

---

## Performance Tips

1. **Async Training** - Backend runs training in background thread, frontend not blocked
2. **Caching** - Use browser cache for menu_dataset.js (doesn't change often)
3. **Connection Pooling** - Flask handles multiple requests efficiently
4. **Lazy Loading** - Only load AI features when user clicks them

---

## Security Notes

1. **Frontend running locally** - No authentication needed for development
2. **Backend in production** - Add authentication before deployment:
   ```python
   from flask_jwt_extended import JWTManager, jwt_required
   jwt = JWTManager(app)
   
   @app.route('/api/train', methods=['POST'])
   @jwt_required()
   def train_models():
       # Protected endpoint
   ```

3. **CORS in production** - Restrict to specific origins:
   ```python
   CORS(app, origins=['https://yourdomain.com'])
   ```

4. **Input Validation** - Validate all API inputs (currently basic)

---

## Next Steps

1. ✓ Start backend: `python backend_server.py`
2. ✓ Run tests: `python test_connection.py`
3. ✓ Open frontend: `student.html`
4. ✓ Try "Train AI" button
5. ✓ Check training results
6. ✓ Test other features (voice, image, recommendations)

**System is ready for full end-to-end testing!**
