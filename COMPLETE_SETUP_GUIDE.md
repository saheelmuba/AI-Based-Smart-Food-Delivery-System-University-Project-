# Frontend-Backend Connection Complete Setup

## 📦 Files Structure Overview

```
FRONTEND (HTML/JS/CSS)          BACKEND (Python)           DATA
━━━━━━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━        ━━━━━
student.html ─┐                backend_server.py          menu_dataset.csv
student.js   ├──→ HTTP API ←──→ training_pipeline.py     orders data
student.css  │   (Port 5000)    menu_recommender.py       (localStorage)
menu_dataset.js ┘                unified_food_system.py
                                food_ai_config.py
```

---

## 🚀 STEP 1: Install Python

### Windows:
1. Download: https://www.python.org/downloads/
2. Run installer
3. **IMPORTANT: Check "Add Python to PATH"** ✓
4. Click "Install Now"

### Verify Installation:
```bash
python --version
# Should show: Python 3.8.x or higher
```

---

## 📥 STEP 2: Install Backend Dependencies

### Run this command in terminal/PowerShell:
```bash
cd "c:\Users\Saheel Muba\Documents\ai project"
pip install -r requirements_backend.txt
```

This installs:
- Flask 3.0.0 (web framework)
- pandas 2.1.0 (data processing)
- scikit-learn 1.3.0 (machine learning)
- flask-cors 4.0.0 (cross-origin support)
- Plus other AI libraries

### Verify Installation:
```bash
python -c "import flask, pandas, sklearn; print('✓ All dependencies installed')"
```

---

## ✅ STEP 3: Verify System Setup

Run the verification script:
```bash
python verify_system.py
```

Expected output:
```
✓ Python version: 3.9+
✓ Dependencies: All installed
✓ AI modules: Found
✓ Menu data: Loaded (53 items)
✓ Backend server: Can import
✓ Port 5000: Available
✓ Directories: Created
✓ Training pipeline: Ready
✓ Menu data: Verified
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASS: 8/8 tests passed ✓
```

---

## 🔌 STEP 4: Start Backend Server

### Option A: Quick Start
```bash
python backend_server.py
```

Expected output:
```
* Running on http://127.0.0.1:5000
* Debug mode: on
🚀 Backend server listening on 0.0.0.0:5000
```

### Option B: Use Batch File (Windows)
```bash
SETUP_AND_RUN.bat
```

### Option C: Production Mode (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend_server:app
```

**Keep this terminal running while using the frontend!**

---

## 🌐 STEP 5: Open Frontend

Open your browser and navigate to:
```
file:///c:/Users/Saheel%20Muba/Documents/ai%20project/student.html
```

Or use Python's built-in server:
```bash
# In another terminal, in the ai project folder
python -m http.server 8000

# Then visit: http://localhost:8000/student.html
```

---

## 🧪 STEP 6: Test Connection

In a third terminal, run:
```bash
python test_connection.py
```

This will test:
1. ✓ Backend server is running
2. ✓ CORS headers are set
3. ✓ All API endpoints respond
4. ✓ Training endpoint accepts requests
5. ✓ Frontend files are valid
6. ✓ HTML structure is correct
7. ✓ Backend dependencies are present

Expected output:
```
============================================================
Step 1: Backend Server Status
============================================================
✓ Backend server is running on http://localhost:5000
ℹ Response: { "status": "healthy", "version": "1.0.0" }

============================================================
Step 2: CORS Headers
============================================================
✓ Access-Control-Allow-Origin: *
✓ CORS is properly configured

[... more tests ...]

============================================================
Test Summary
============================================================
Total Tests: 7
Passed: 7
✓ All tests passed! Frontend-Backend connection is ready.
```

---

## 🎯 STEP 7: Test Frontend-Backend Connection

### Via Chat Interface:
1. Open `student.html` in browser
2. Click "Demo Access" to log in
3. Click chat bubble (bottom right)
4. Click "Train AI" button or type: `train`
5. Watch the chat respond with training status

### Via API Directly:
```bash
# Test health
curl http://localhost:5000/api/health

# Test status
curl http://localhost:5000/api/status

# Send training request
curl -X POST http://localhost:5000/api/train ^
  -H "Content-Type: application/json" ^
  -d "{\"menu\": [], \"orders\": [], \"language\": \"en-US\", \"timestamp\": \"\"}"
```

---

## 🔄 Complete Workflow

```
Terminal 1: Start Backend Server
  $ python backend_server.py
  * Running on http://127.0.0.1:5000
  [waiting for requests...]

Terminal 2: Test Connection
  $ python test_connection.py
  ✓ All tests passed

Terminal 3: Monitor (Optional)
  $ watch "curl -s http://localhost:5000/api/status"

Browser: Open Frontend
  URL: file:///c:/Users/Saheel Muba/Documents/ai project/student.html
  [student.html loads]
  [student.js connects to backend]
  [chat interface appears]

User Action: Click "Train AI"
  ↓
Frontend: sendTrainingRequest() called
  ↓
HTTP: POST /api/train
  ↓
Backend: Receives request, starts training in background
  ↓
HTTP 202: Returns "training" status
  ↓
Frontend: Chat shows "Training started..."
  ↓
Backend: Trains models (45-60 seconds)
  ↓
Results: Saved to training_results/ folder

User: Checks status
  ↓
Frontend: Click chat or check /api/status
  ↓
Backend: Returns current training state
  ↓
Frontend: Chat shows "Training complete"
```

---

## 📊 API Endpoints Reference

All available at: `http://localhost:5000`

### GET /api/health
```bash
curl http://localhost:5000/api/health
# Response: { "status": "healthy", "version": "1.0.0" }
```

### GET /api/status
```bash
curl http://localhost:5000/api/status
# Response: { "training": {...}, "features": {...} }
```

### POST /api/train
```bash
curl -X POST http://localhost:5000/api/train \
  -H "Content-Type: application/json" \
  -d '{"menu": [...], "orders": [...], "language": "en-US", "timestamp": ""}'
# Response: { "status": "training", "training_id": "TRAIN_..." }
```

### POST /api/recommend
```bash
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "dietary_preference": "all", "language": "en-US"}'
# Response: { "recommendations": [...] }
```

---

## 🛠️ Troubleshooting

### Error: "Python is not recognized"
```
Solution: Python is not in PATH
1. Uninstall Python (Control Panel → Programs)
2. Download from python.org
3. Run installer again
4. CHECK "Add Python to PATH" ✓
5. Restart PowerShell/Command Prompt
```

### Error: "Port 5000 already in use"
```
Solution: Another process is using port 5000
1. Find the process:
   netstat -ano | findstr :5000
2. Kill it:
   taskkill /PID <PID> /F
3. Or use different port in backend_server.py:
   app.run(..., port=5001, ...)
```

### Error: "ModuleNotFoundError: No module named 'flask'"
```
Solution: Dependencies not installed
1. Run: pip install -r requirements_backend.txt
2. Verify: python -c "import flask"
3. Try again: python backend_server.py
```

### Error: "Failed to fetch" in browser
```
Solution: Backend not running or wrong URL
1. Check terminal shows "Running on http://127.0.0.1:5000"
2. Test: curl http://localhost:5000/api/health
3. If fails: Start backend with python backend_server.py
```

### Error: "CORS error" in browser console
```
Solution: Backend CORS not configured
1. Check backend_server.py has "CORS(app)"
2. Backend should have:
   from flask_cors import CORS
   CORS(app)
3. Restart backend: python backend_server.py
```

### Training never completes
```
Solution: Check training status
1. Terminal 1: Check backend logs for errors
2. Terminal 3: curl http://localhost:5000/api/status
3. Look for "is_training": false to confirm completion
4. Check training_results/ folder for output files
```

---

## 📁 File Connections Explained

### Frontend → Backend Path
```
student.html
  └─ loads student.js
     └─ loads menu_dataset.js
        └─ MENU array available
     └─ defines sendTrainingRequest()
        └─ calls fetch('/api/train')
           └─ connects to backend_server.py
              └─ /api/train route handler
                 └─ imports training_pipeline.py
                    └─ runs CampusDataTrainingPipeline
                       └─ trains models
                          └─ saves results to JSON
```

### Key Connection Functions

**student.js:**
```javascript
// 1. Converts MENU to JSON
const payload = { menu: MENU, orders: orderHistory, ... };

// 2. Sends to backend
fetch('/api/train', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})

// 3. Receives response
.then(res => res.json())
.then(data => { 
  // data.training_id = "TRAIN_20260526_120000"
  // data.status = "training"
})
```

**backend_server.py:**
```python
@app.route('/api/train', methods=['POST'])
def train_models():
    data = request.json  # Gets payload from frontend
    
    training_id = generate_training_id()
    
    # Start async training
    thread = threading.Thread(
        target=_run_training,
        args=(data['menu'], data['orders'], data['language'])
    )
    thread.daemon = True
    thread.start()
    
    # Return immediately with 202 Accepted
    return jsonify({
        'status': 'training',
        'training_id': training_id
    }), 202
```

---

## 💡 Usage Examples

### Example 1: Train AI from Chat
```
1. Open student.html
2. Login with demo
3. Click chat bubble
4. Click "Train AI" quick-reply
5. Chat shows: "Training started..."
6. Wait 45-60 seconds
7. Chat shows: "Training complete..."
```

### Example 2: Use Voice Commands
```
1. Open student.html
2. Go to "AI Features" page
3. Click "Voice Ordering"
4. Click "Start Listening"
5. Say: "Order 2 Chicken Briyani"
6. Item added to cart
```

### Example 3: Get Recommendations
```
1. Open student.html
2. Click chat bubble
3. Type: "What do you recommend?"
4. Chat responds with AI recommendations
5. Click item to add to cart
```

### Example 4: Upload Menu Data
```
1. Open student.html
2. Go to "Upload" page
3. Click "Upload Data Files"
4. Select CSV with new menu items
5. Click "Apply Data to Menu & Ads"
6. Chat shows training started
7. New items added to menu
```

---

## 🔐 Security Notes

- **Development**: CORS allows all origins (CORS(app))
- **Production**: Restrict CORS to specific domain
- **Authentication**: Add JWT token verification for /api/train
- **Input Validation**: Currently minimal, add before production
- **HTTPS**: Use HTTPS (not HTTP) in production

---

## 📈 Performance

- **Backend**: Flask with threading (single process)
- **Training**: Async in background thread (non-blocking)
- **Frontend**: Vanilla JS (fast, lightweight)
- **Database**: Currently CSV files (can upgrade to MongoDB)

**For production scalability:**
- Use Gunicorn (4+ workers)
- Add Redis for caching
- Use PostgreSQL or MongoDB
- Deploy with Docker

---

## ✨ Features Connected

Frontend ↔ Backend connections:

| Feature | Frontend | Backend |
|---------|----------|---------|
| Train AI | Chat "Train AI" button | POST /api/train |
| Voice Ordering | Voice recognition UI | No endpoint yet |
| Image Recognition | Image upload UI | POST /api/analyze-image |
| Recommendations | Chat responses | POST /api/recommend |
| Status Check | Chat display | GET /api/status |
| Health Check | System startup | GET /api/health |

---

## 🎓 Learning Resources

- Flask: https://flask.palletsprojects.com
- Fetch API: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- CORS: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- Python: https://docs.python.org

---

## 📞 Quick Help

```bash
# Setup
pip install -r requirements_backend.txt

# Verify
python verify_system.py

# Run
python backend_server.py

# Test
python test_connection.py

# Check status
curl http://localhost:5000/api/status

# Open frontend
open student.html  # macOS
start student.html # Windows
xdg-open student.html # Linux
```

---

## ✅ Checklist

- [ ] Python 3.8+ installed with PATH configured
- [ ] Dependencies installed: `pip install -r requirements_backend.txt`
- [ ] System verified: `python verify_system.py`
- [ ] Backend running: `python backend_server.py`
- [ ] Connection tested: `python test_connection.py`
- [ ] Frontend opened: student.html
- [ ] Chat working: "Train AI" button responds
- [ ] Training executes: Chat shows status messages

**All done! System is ready for development and testing.**
