# Quick Backend Reference Guide

## Flask (Current) → Alternative Backends

This guide shows how to migrate or extend the current Flask backend to other frameworks.

---

## 1. Flask API Endpoints (Current Reference)

All backends should implement these endpoints identically:

### POST /api/train
```json
Request:
{
  "menu": [{id, name, price, category, veg, calories, protein}],
  "orders": [{id, total, items, timestamp}],
  "language": "en-US",
  "timestamp": "ISO8601"
}

Response (HTTP 202):
{
  "status": "training",
  "training_id": "TRAIN_20260526_120000",
  "estimated_time": "45-60 seconds"
}

Async Result (via polling GET /api/status):
{
  "training": {
    "models_available": ["recommendation", "demand_prediction"],
    "metrics": {...}
  }
}
```

### GET /api/status
```json
Response (HTTP 200):
{
  "status": "operational",
  "training": {
    "is_training": false,
    "last_trained": "2026-05-26T12:00:00",
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

### POST /api/recommend
```json
Request:
{
  "user_id": "student123",
  "dietary_preference": "vegetarian",
  "language": "en-US"
}

Response (HTTP 200):
{
  "status": "success",
  "recommendations": [
    {"name": "Rice + Veg Curry", "price": 200, "confidence": 0.92}
  ],
  "confidence": 0.92
}
```

### GET /api/health
```json
Response (HTTP 200):
{
  "status": "healthy",
  "timestamp": "2026-05-26T12:01:00",
  "version": "1.0.0"
}
```

---

## 2. FastAPI Implementation

**Install:**
```bash
pip install fastapi uvicorn python-multipart
```

**backend_server_fastapi.py:**
```python
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import asyncio
import threading
import pandas as pd

app = FastAPI(
    title="ICST AI Smart Food Backend",
    description="FastAPI backend for training AI models",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class MenuItem(BaseModel):
    id: int
    name: str
    price: float
    category: str
    veg: bool
    calories: int
    protein: str

class Order(BaseModel):
    id: str
    total: float
    items: list
    timestamp: str

class TrainingRequest(BaseModel):
    menu: list
    orders: list
    language: str
    timestamp: str

class TrainingResponse(BaseModel):
    status: str
    message: str
    training_id: str
    estimated_time: str

# Global state
training_state = {
    'is_training': False,
    'last_trained': None,
    'training_status': 'idle',
    'models_available': [],
    'metrics': {},
}

@app.post("/api/train", response_model=TrainingResponse, status_code=202)
async def train_models(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Train AI models with campus menu and order history"""
    
    if training_state['is_training']:
        return TrainingResponse(
            status="training",
            message="Training already in progress",
            training_id=training_state.get('current_training_id', 'UNKNOWN'),
            estimated_time=""
        )
    
    training_id = f"TRAIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    training_state['is_training'] = True
    training_state['current_training_id'] = training_id
    
    # Add to background tasks (FastAPI preferred approach)
    background_tasks.add_task(
        _run_training,
        menu_data=request.menu,
        orders=request.orders,
        language=request.language,
        training_id=training_id
    )
    
    return TrainingResponse(
        status="training",
        message=f"Training started with ID: {training_id}",
        training_id=training_id,
        estimated_time="45-60 seconds"
    )

async def _run_training(menu_data, orders, language, training_id):
    """Background training task"""
    try:
        print(f"🚀 Training started: {training_id}")
        training_state['training_status'] = 'preprocessing'
        
        # Simulate training
        await asyncio.sleep(5)
        
        menu_df = pd.DataFrame(menu_data)
        order_df = pd.DataFrame(orders) if orders else pd.DataFrame()
        
        training_state['training_status'] = 'training_complete'
        training_state['models_available'] = ['recommendation', 'demand_prediction']
        training_state['metrics'] = {
            'demand': {
                'total_orders': len(order_df),
                'average_order_value': float(order_df['total'].mean()) if 'total' in order_df.columns else 0,
            }
        }
        
        print(f"✓ Training complete: {training_id}")
        training_state['last_trained'] = datetime.now().isoformat()
        training_state['is_training'] = False
        training_state['training_status'] = 'idle'
    
    except Exception as e:
        print(f"❌ Training failed: {e}")
        training_state['is_training'] = False
        training_state['training_status'] = 'error'

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "training": training_state,
        "campus": "ICST University Park",
        "features": {
            "voice_ordering": True,
            "image_recognition": True,
            "demand_forecasting": True,
            "recommendations": True,
            "multilingual": True,
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/recommend")
async def get_recommendations(payload: dict):
    """Get AI recommendations"""
    return {
        "status": "success",
        "recommendations": [
            {"name": "Chicken Briyani", "price": 350, "confidence": 0.92}
        ],
        "confidence": 0.92,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
```

**Run:**
```bash
python backend_server_fastapi.py

# Auto-generated API docs
# Open http://localhost:5000/docs (Swagger UI)
# Or http://localhost:5000/redoc (ReDoc)
```

**Key FastAPI advantages:**
- ✅ Automatic OpenAPI documentation
- ✅ Built-in request validation
- ✅ Native async/await support
- ✅ Type hints for better IDE support

---

## 3. Node.js + Express Implementation

**Install:**
```bash
npm init -y
npm install express cors body-parser
```

**backend_server.js:**
```javascript
const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// Global state
const trainingState = {
  isTraining: false,
  lastTrained: null,
  trainingStatus: 'idle',
  modelsAvailable: [],
  metrics: {}
};

// POST /api/train
app.post('/api/train', (req, res) => {
  if (trainingState.isTraining) {
    return res.status(202).json({
      status: 'training',
      message: 'Training already in progress',
      training_id: trainingState.currentTrainingId
    });
  }

  const trainingId = `TRAIN_${new Date().toISOString().replace(/[^0-9]/g, '')}`;
  trainingState.isTraining = true;
  trainingState.currentTrainingId = trainingId;
  trainingState.trainingStatus = 'initializing';

  // Respond immediately
  res.status(202).json({
    status: 'training',
    message: `Training started with ID: ${trainingId}`,
    training_id: trainingId,
    estimated_time: '45-60 seconds'
  });

  // Run training in background (spawn Python process)
  const python = spawn('python', ['training_pipeline.py']);
  
  python.stdout.on('data', (data) => {
    console.log(`[Training] ${data}`);
  });

  python.on('close', (code) => {
    console.log(`Training process exited with code ${code}`);
    trainingState.isTraining = false;
    trainingState.lastTrained = new Date().toISOString();
    trainingState.trainingStatus = 'idle';
    trainingState.modelsAvailable = ['recommendation', 'demand_prediction'];
  });
});

// GET /api/status
app.get('/api/status', (req, res) => {
  res.json({
    status: 'operational',
    timestamp: new Date().toISOString(),
    training: trainingState,
    campus: 'ICST University Park',
    features: {
      voice_ordering: true,
      image_recognition: true,
      demand_forecasting: true,
      recommendations: true,
      multilingual: true
    }
  });
});

// GET /api/health
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// POST /api/recommend
app.post('/api/recommend', (req, res) => {
  res.json({
    status: 'success',
    recommendations: [
      { name: 'Chicken Briyani', price: 350, confidence: 0.92 }
    ],
    confidence: 0.92,
    timestamp: new Date().toISOString()
  });
});

const PORT = 5000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Backend server running on http://0.0.0.0:${PORT}`);
});
```

**Run:**
```bash
node backend_server.js
```

**Note:** Node.js is best for spawning Python subprocesses for ML tasks. Not recommended as primary backend for this project.

---

## 4. Go + Gin Implementation

**Install:**
```bash
go mod init backend
go get github.com/gin-gonic/gin
```

**backend_server.go:**
```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os/exec"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

type TrainingRequest struct {
	Menu      []interface{} `json:"menu"`
	Orders    []interface{} `json:"orders"`
	Language  string        `json:"language"`
	Timestamp string        `json:"timestamp"`
}

type TrainingResponse struct {
	Status        string `json:"status"`
	Message       string `json:"message"`
	TrainingID    string `json:"training_id"`
	EstimatedTime string `json:"estimated_time"`
}

var (
	trainingState = map[string]interface{}{
		"isTraining":       false,
		"lastTrained":      nil,
		"trainingStatus":   "idle",
		"modelsAvailable": []string{},
		"metrics":         map[string]interface{}{},
	}
	stateMutex sync.Mutex
)

func main() {
	router := gin.Default()

	// CORS
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// Endpoints
	router.POST("/api/train", trainModels)
	router.GET("/api/status", getStatus)
	router.GET("/api/health", healthCheck)
	router.POST("/api/recommend", getRecommendations)

	log.Println("🚀 Backend server running on http://0.0.0.0:5000")
	router.Run(":5000")
}

func trainModels(c *gin.Context) {
	var req TrainingRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	stateMutex.Lock()
	isTraining := trainingState["isTraining"].(bool)
	stateMutex.Unlock()

	if isTraining {
		c.JSON(202, gin.H{
			"status":      "training",
			"message":     "Training already in progress",
			"training_id": trainingState["currentTrainingID"],
		})
		return
	}

	trainingID := "TRAIN_" + time.Now().Format("20060102_150405")

	stateMutex.Lock()
	trainingState["isTraining"] = true
	trainingState["currentTrainingID"] = trainingID
	stateMutex.Unlock()

	c.JSON(202, TrainingResponse{
		Status:        "training",
		Message:       "Training started with ID: " + trainingID,
		TrainingID:    trainingID,
		EstimatedTime: "45-60 seconds",
	})

	// Background training (spawn Python)
	go runTraining(trainingID, req)
}

func runTraining(trainingID string, req TrainingRequest) {
	// Call Python training pipeline
	cmd := exec.Command("python", "training_pipeline.py")
	err := cmd.Run()
	
	stateMutex.Lock()
	trainingState["isTraining"] = false
	trainingState["lastTrained"] = time.Now().Format(time.RFC3339)
	trainingState["trainingStatus"] = "idle"
	trainingState["modelsAvailable"] = []string{"recommendation", "demand_prediction"}
	stateMutex.Unlock()

	if err != nil {
		log.Printf("❌ Training failed: %v", err)
	} else {
		log.Printf("✓ Training complete: %s", trainingID)
	}
}

func getStatus(c *gin.Context) {
	stateMutex.Lock()
	state := trainingState
	stateMutex.Unlock()

	c.JSON(200, gin.H{
		"status":    "operational",
		"timestamp": time.Now().Format(time.RFC3339),
		"training":  state,
		"campus":    "ICST University Park",
		"features": map[string]bool{
			"voice_ordering":      true,
			"image_recognition":   true,
			"demand_forecasting":  true,
			"recommendations":     true,
			"multilingual":        true,
		},
	})
}

func healthCheck(c *gin.Context) {
	c.JSON(200, gin.H{
		"status":    "healthy",
		"timestamp": time.Now().Format(time.RFC3339),
		"version":   "1.0.0",
	})
}

func getRecommendations(c *gin.Context) {
	c.JSON(200, gin.H{
		"status": "success",
		"recommendations": []map[string]interface{}{
			{
				"name":       "Chicken Briyani",
				"price":      350,
				"confidence": 0.92,
			},
		},
		"confidence": 0.92,
		"timestamp":  time.Now().Format(time.RFC3339),
	})
}
```

**Run:**
```bash
go run backend_server.go
```

---

## Migration Checklist

If switching backends, ensure all these are implemented:

- [ ] POST /api/train endpoint (returns 202, runs async)
- [ ] GET /api/status endpoint (returns training state)
- [ ] GET /api/health endpoint
- [ ] POST /api/recommend endpoint
- [ ] POST /api/analyze-image endpoint
- [ ] CORS headers enabled
- [ ] Async training task (background thread/goroutine)
- [ ] Error handling & logging
- [ ] Frontend configured to use new backend URL
- [ ] Port 5000 (or updated in frontend)

---

## Frontend Configuration

**Update URL in student.js if backend changes:**

```javascript
// Current (Flask on localhost)
const BACKEND_URL = 'http://localhost:5000';

// Or set via environment
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';
```

All frameworks should serve on port 5000 or update the frontend accordingly.

---

## Summary

| Framework | Complexity | Setup Time | ML Integration | Recommendation |
|-----------|-----------|-----------|---|---|
| **Flask** | Low | 5 min | ✅ Excellent | ✅ USE THIS |
| FastAPI | Low | 5 min | ✅ Excellent | ✅ Alternative |
| Node.js | Medium | 10 min | ⚠️ Via subprocess | ⚠️ Not recommended |
| Go | Medium | 15 min | ⚠️ Via subprocess | ⚠️ Not recommended |
| Django | High | 20 min | ✅ Excellent | ✅ If scaling |

**Stick with Flask for now. Migrate to FastAPI if performance becomes an issue.**
