@echo off
echo Starting AI Resume Analyzer Backend API...
cd App
start cmd /k "..\venvapp\Scripts\activate.bat && python -m uvicorn api:app --reload --port 8000"
cd ..

echo Starting Frontend Server...
cd frontend
start cmd /k "python -m http.server 3000"
