#!/bin/bash
# ── Development runner — starts both API and frontend ──

set -e

echo "================================================"
echo "  Synthera - Multi-Agent Research & Intelligence Platform"
echo "================================================"
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo "No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "   Please edit .env with your API keys before running."
    exit 1
fi

# Start FastAPI backend
echo "Starting FastAPI backend on port 8000..."
uvicorn synthera.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "  Backend PID: $API_PID"

# Wait for API to be ready
echo "Waiting for API to start..."
sleep 3

# Start Streamlit frontend
echo "Starting Streamlit frontend on port 8501..."
streamlit run frontend/app.py --server.port 8501 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

echo ""
echo "================================================"
echo "  Services running:"
echo "    API:      http://localhost:8000"
echo "    API Docs: http://localhost:8000/docs"
echo "    Frontend: http://localhost:8501"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop all services."

# Trap Ctrl+C to clean up both processes
trap "echo 'Shutting down...'; kill $API_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for either process to exit
wait
