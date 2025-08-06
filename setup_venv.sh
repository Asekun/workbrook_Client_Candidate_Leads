#!/bin/bash

# Virtual Environment Setup Script for FastAPI Job Scraper

echo "🐍 Setting up Python Virtual Environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "📦 Creating new virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install ChromeDriver
echo "🔧 Installing ChromeDriver..."
# ChromeDriver will be automatically managed by webdriver-manager

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Run the application: uvicorn main:app --reload"
echo "   3. Test the API: python test_scraper.py"
echo ""
echo "💡 Tip: You can also use ./start.sh to automatically start the server" 