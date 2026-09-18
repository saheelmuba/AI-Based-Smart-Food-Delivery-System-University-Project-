#!/bin/bash
# Quick Start Script for ICST AI Smart Food Backend Server (Linux/Mac)
# Run: chmod +x start_server.sh && ./start_server.sh

cd "$(dirname "$0")"

echo ""
echo "========================================"
echo "ICST AI Smart Food - Backend Server"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if requirements are installed
echo "Checking dependencies..."
python3 -c "import flask, pandas, sklearn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠ Dependencies not installed. Installing now..."
    pip3 install -r requirements_backend.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo "✓ All dependencies installed"
echo ""

# Check if menu data exists
if [ ! -f "menu_dataset.csv" ]; then
    echo "ERROR: menu_dataset.csv not found"
    echo "Please ensure you're in the correct directory"
    exit 1
fi

echo "✓ Menu data found"
echo ""

# Start the server
echo ""
echo "========================================"
echo "Starting Backend Server..."
echo "========================================"
echo ""
echo "Server will be available at:"
echo "  • http://localhost:5000"
echo "  • http://0.0.0.0:5000 (network)"
echo ""
echo "Endpoints:"
echo "  POST   /api/train        - Train models"
echo "  GET    /api/status       - Check status"
echo "  POST   /api/recommend    - Get recommendations"
echo "  POST   /api/analyze-image - Analyze food"
echo "  GET    /api/health       - Health check"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 backend_server.py
