#!/bin/bash

# Start the Latin Adaptive Learning Backend Server

echo "🚀 Starting Latin Adaptive Learning Backend..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and add your Anthropic API key"
    exit 1
fi

# Check if API key is set
if grep -q "your_api_key_here" .env; then
    echo "⚠️  Warning: Please add your Anthropic API key to .env file"
    echo "   Edit line 4: ANTHROPIC_API_KEY=your_api_key_here"
    echo ""
    read -p "Press Enter once you've added your API key..."
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/Scripts/activate

# Start the server
echo "✨ Starting Uvicorn server on http://localhost:8000"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "❤️  Health Check: http://localhost:8000/health"
echo ""
echo "Press CTRL+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

uvicorn app.main:app --reload
