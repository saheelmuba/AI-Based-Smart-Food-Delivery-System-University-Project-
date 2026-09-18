@echo off
REM ICST AI Food Ordering System - one-command launcher (Windows)
cd /d "%~dp0"
echo Installing dependencies (Flask, Flask-CORS, Pillow)...
python -m pip install -r requirements.txt
echo.
echo Starting backend on http://localhost:5000
echo Open http://localhost:5000 in Chrome or Edge (voice needs one of these).
python app.py
