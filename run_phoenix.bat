@echo off
title Phoenix AI Launcher
echo ===================================================
echo             Phoenix AI Launcher v1.0
echo ===================================================
echo.

echo [1/3] Starting FastAPI Backend...
start "Phoenix AI Backend" cmd /k ".venv\Scripts\python -m uvicorn ai_project.api.main:app --host 127.0.0.1 --port 8000"

echo Waiting for backend to initialize (5s)...
timeout /t 5 /nobreak >nul

echo.
echo [2/3] Starting React Frontend...
cd ai_project\dashboard
start "Phoenix AI Frontend" cmd /k "npm run dev"

echo.
echo [3/3] Opening dashboard in browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173/

echo.
echo ===================================================
echo Phoenix AI is running!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173/
echo ===================================================
echo Close the newly opened command windows to stop the servers.
pause
