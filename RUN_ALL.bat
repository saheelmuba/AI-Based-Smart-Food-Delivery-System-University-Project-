@echo off
REM ============================================
REM ICST AI Smart Food - Start Backend and UI
REM ============================================

cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo Installing required backend and UI dependencies...
python install_venv_deps.py

echo Starting backend server on http://localhost:5000...
start "AI Food Backend" cmd /k "python backend_server.py"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo Starting web UI on http://localhost:5001...
start "AI Food UI" cmd /k "python food_ai_app.py"

echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5001
echo.
echo Press Ctrl+C in each window to stop the servers.
pause
