#!/bin/bash

# Virtual Environment Activation Script

echo "🐍 Activating Python Virtual Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "📦 Please run ./setup_venv.sh first to create the virtual environment."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo ""
echo "📋 Available commands:"
echo "   uvicorn main:app --reload          # Start development server"
echo "   python test_scraper.py             # Test the API"
echo "   pip list                           # List installed packages"
echo "   deactivate                         # Deactivate virtual environment"
echo ""
echo "🌐 Server will be available at: http://localhost:8000"
echo "📚 API docs will be available at: http://localhost:8000/docs"
echo ""

# Start a new shell with the virtual environment activated
exec $SHELL 