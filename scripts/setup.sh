#!/bin/bash
# Wiko Defect Analyzer - Setup Script
# Run this after downloading the project files

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     WIKO DEFECT ANALYZER - SETUP                          ║"
echo "║     GPT-5.2 Edition                                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "→ Checking Python version..."
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.11+"; exit 1; }

# Create virtual environment
echo "→ Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "→ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "→ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "→ Installing dependencies..."
pip install -r requirements.txt

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    echo "→ Creating .env from template..."
    cp .env.template .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your Azure credentials!"
    echo "   Open .env and fill in:"
    echo "   - AZURE_AI_PROJECT_ENDPOINT"
    echo "   - AZURE_AI_API_KEY"
    echo ""
fi

# Create directories
mkdir -p logs
mkdir -p test_images
mkdir -p reports

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Azure AI Foundry credentials"
echo "2. Add test images to test_images/"
echo "3. Run: source venv/bin/activate"
echo "4. Test: python -m agents.defect_analyzer_gpt52"
echo ""
