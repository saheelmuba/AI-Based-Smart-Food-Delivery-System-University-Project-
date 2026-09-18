@echo off
REM Quick Start Script for ICST AI Smart Food Backend Server
REM Run this to start the backend with one command

cd /d "%~dp0"

echo.
echo ========================================
echo ICST AI Smart Food - Backend Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo ✓ Python found
echo.

REM Check if requirements are installed
echo Checking dependencies...
python -c "import flask, pandas, sklearn" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠ Dependencies not installed. Installing now...
    pip install -r requirements_backend.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✓ All dependencies installed
echo.

REM Check if menu data exists
if not exist "menu_dataset.csv" (
    echo ERROR: menu_dataset.csv not found
    echo Please ensure you're in the correct directory
    pause
    exit /b 1
)

echo ✓ Menu data found
echo.

REM Start the server
echo.
echo ========================================
echo Starting Backend Server...
echo ========================================
echo.
echo Server will be available at:
echo   • http://localhost:5000
echo   • http://0.0.0.0:5000 (network)
echo.
echo Endpoints:
echo   POST   /api/train        - Train models
echo   GET    /api/status       - Check status
echo   POST   /api/recommend    - Get recommendations
echo   POST   /api/analyze-image - Analyze food
echo   GET    /api/health       - Health check
echo.
echo Press Ctrl+C to stop the server
echo.

python backend_server.py

pause
