#!/usr/bin/env bash

# Atman - Uploaded Brain: One-Command Launch Script

# Exit immediately if a command exits with a non-zero status
set -e

echo "🧠 Starting Atman Environment..."

# 1. Setup Python Backend
echo "--> Checking Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "--> Installing backend dependencies..."
pip install -r requirements.txt -q

export PYTHONPATH="$PWD/backend"

# 2. Setup Node.js Frontend
echo "--> Checking Frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
cd ..

# 3. Launch Services
echo "--> Launching Server & Frontend..."

# Function to properly kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}
trap cleanup SIGINT SIGTERM

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

cd frontend
npm run dev -- --port 5173 &
FRONTEND_PID=$!

echo "==========================================================="
echo " Atman Running! 🧠"
echo " -> Frontend: http://localhost:5173"
echo " -> Backend APIs: http://localhost:8000/docs"
echo " Press Ctrl+C to stop both servers."
echo "==========================================================="

wait $BACKEND_PID
wait $FRONTEND_PID
