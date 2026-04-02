#!/bin/bash

# LLM Speed Monitor Startup Script

set -e

echo "🚀 Starting LLM Speed Monitor..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found."
    echo "   Please copy .env.example to .env and fill in your API keys:"
    echo "   cp .env.example .env"
    exit 1
fi

# Start collector in background
echo "📊 Starting collector..."
python -m collector.main &
COLLECTOR_PID=$!

# Trap to cleanup on exit
trap "echo 'Stopping...'; kill $COLLECTOR_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Start dashboard
echo "📈 Starting dashboard..."
echo "   Access at: http://localhost:8501"
streamlit run dashboard/app.py
