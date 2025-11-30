@echo off
echo Starting Dual-LLM Web App...

echo Installing Python dependencies...
pip install -q fastapi uvicorn requests

echo Starting Backend...
start "Dual-LLM Backend" cmd /k "cd web_app/backend && python main.py"

echo Starting Frontend...
cd web_app/frontend
start "Dual-LLM Frontend" cmd /k "npm run dev"

echo Done! Check the opened windows.
