@echo off
REM ============================================
REM ICST AI Smart Food - Complete Setup
REM ============================================

echo.
echo ========================================
echo  ICST AI Smart Food - Setup Guide
echo ========================================
echo.

REM Check if Python is installed
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Download Python from: https://www.python.org/downloads/
    echo Make sure to CHECK "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)
python --version

echo.
echo [2/5] Checking backend dependencies...
python -c "import flask; print('✓ Flask installed')" 2>nul
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements_backend.txt
)

echo.
echo [3/5] Verifying system setup...
python verify_system.py
if %errorlevel% neq 0 (
    echo WARNING: Some checks failed. See details above.
)

echo.
echo [4/5] Backend status...
echo Checking if port 5000 is available...
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo WARNING: Port 5000 is already in use
    echo You may need to stop the other process
)

echo.
echo [5/5] Starting Backend Server...
echo.
echo Starting Flask server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python backend_server.py
