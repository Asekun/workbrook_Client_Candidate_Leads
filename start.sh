#!/bin/bash

# FastAPI Job Scraper Startup Script

echo "🚀 Starting FastAPI Job Scraper..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please ensure you're in the correct directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created!"
else
    echo "✅ Virtual environment already exists!"
fi

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

echo "✅ Setup complete!"
echo ""
echo "🌐 Starting FastAPI server..."
echo "   The API will be available at: http://localhost:8000"
echo "   API documentation: http://localhost:8000/docs"
echo ""
echo "📝 To test the API, run: python test_scraper.py"
echo ""

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000 