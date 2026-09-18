@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found. Run: python -m venv .venv
  echo Then: .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
set FLASK_OPEN_BROWSER=1
python app.py
pause
