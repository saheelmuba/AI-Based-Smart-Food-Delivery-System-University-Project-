AI-Based Smart Food Delivery System

This repository contains components for an AI Smart Food Delivery system: food image recognition, spoilage detection, recipe lookup, and a small web UI.

Overview
- Web UI: `food_ai_app.py` (Flask)
- Food recognition: `food_image_recognizer.py` (Google Vision fallback + local model)
- Spoilage detector: `spoilage_detector.py` (PyTorch)
- Recipe lookup: `recipe_lookup.py` (Edamam fallback to local menu)
- Training: `train_models.py` (train food recognizer and spoilage detector)

Quickstart
1. Install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements_backend.txt
```

2. Create `.env` or set environment variables for external APIs (optional):
- `GOOGLE_APPLICATION_CREDENTIALS` (path to Google service account json)
- `EDAMAM_APP_ID` and `EDAMAM_API_KEY`

See `.env.example` for names.

3. Train models (optional but recommended):

Train only spoilage detector (uses images under `food_data/datasets`):

```bash
python train_models.py --train_spoilage --epochs 10 --device cpu
```

Train food recognizer (downloads Food-101 dataset):

```bash
python train_models.py --train_food --epochs 3 --device cpu
```

4. Run the web app (development):

```bash
python food_ai_app.py
```

API Endpoints
- `GET /` web interface
- `POST /api/analyze` multipart form with `file` key - returns JSON with `food_items`, `spoilage_status`, `confidence`, `ingredients`.
- `GET /api/health` health check

FastAPI inference server
 - `POST /predict` multipart form upload (`file`) — returns same JSON structure
 - `GET /health` health check

Containerization
 - Build image:

```bash
docker build -t ai-food-system:latest .
```

 - Run with compose:

```bash
docker compose up --build
```

Next steps
- Provide API keys for Edamam/Spoonacular/Google Vision for better enrichment and recognition.
- Add more labeled spoilage images under `food_data/datasets/spoilage_images` and `good_food_images`.
- Optionally containerize with Docker for deployment.

Dataset preparation & evaluation

- Prepare unlabeled images in a folder (e.g., `data_pool/`) and auto-export CSV for manual labeling:

```bash
python prepare_spoilage_dataset.py --scan data_pool --export-csv labels.csv
```

- After labeling `labels.csv` (filename,label), apply labels to move files into dataset directories:

```bash
python prepare_spoilage_dataset.py --apply labels.csv
```

- Evaluate spoilage detector (requires trained model or uses heuristic fallback):

```bash
python evaluate_spoilage.py
```

