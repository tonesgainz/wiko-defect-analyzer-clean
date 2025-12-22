#!/bin/bash
# Wiko Defect Analyzer - Flask Server Startup Script

cd "/Users/tonyadmin/wiko-defect-analyzer 2"

# Activate virtual environment
source venv/bin/activate

# Start Flask server
echo "Starting Wiko Defect Analyzer API Server..."
python3 app.py
