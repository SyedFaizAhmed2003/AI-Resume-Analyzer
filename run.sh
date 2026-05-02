#!/bin/bash
echo "Starting AI Resume Analyzer Backend API..."
cd App
python -m uvicorn api:app --reload --port 8000 &
cd ..

echo "Starting Frontend Server..."
cd frontend
python -m http.server 3000
