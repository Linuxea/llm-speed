#!/bin/bash

# LLM Speed Monitor Startup Script
# Usage: ./start.sh [backend|streamlit|nextjs|all]

set -e

MODE=${1:-streamlit}

echo "🚀 Starting LLM Speed Monitor..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found."
    echo "   Please copy .env.example to .env and fill in your API keys:"
    echo "   cp .env.example .env"
    exit 1
fi

# PIDs to cleanup
PIDS=""

cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    for pid in $PIDS; do
        kill $pid 2>/dev/null || true
    done
    exit 0
}

trap cleanup SIGINT SIGTERM

start_backend() {
    echo "🔧 Starting FastAPI backend..."
    python -m api.main &
    PIDS="$PIDS $!"
    sleep 2
    echo "   API running at: http://localhost:8000"
}

start_collector() {
    echo "📊 Starting collector..."
    python -m collector.main &
    PIDS="$PIDS $!"
}

start_streamlit() {
    echo "📈 Starting Streamlit dashboard..."
    echo "   Access at: http://localhost:8501"
    streamlit run dashboard/app.py &
    PIDS="$PIDS $!"
}

start_nextjs() {
    echo "🎨 Starting Next.js dashboard..."
    cd web
    npm run dev &
    PIDS="$PIDS $!"
    cd ..
    echo "   Access at: http://localhost:3000"
}

case $MODE in
    backend)
        start_backend
        start_collector
        ;;
    streamlit)
        start_backend
        start_collector
        start_streamlit
        ;;
    nextjs)
        start_backend
        start_collector
        start_nextjs
        ;;
    all)
        start_backend
        start_collector
        start_streamlit
        sleep 2
        start_nextjs
        ;;
    *)
        echo "Usage: $0 [backend|streamlit|nextjs|all]"
        echo "  backend  - API + collector only"
        echo "  streamlit - Streamlit frontend (default)"
        echo "  nextjs   - Next.js frontend"
        echo "  all      - Both frontends"
        exit 1
        ;;
esac

echo ""
echo "✅ Services started! Press Ctrl+C to stop."
echo ""

# Keep script running
wait
