#!/bin/bash

# Start the FastAPI backend server
echo "Starting FastAPI server..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start the Vite frontend development server
echo "Starting Vite server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both processes to exit
wait $BACKEND_PID
wait $FRONTEND_PID
