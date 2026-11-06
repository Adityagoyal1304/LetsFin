@echo off
echo ===================================================
echo Starting LetsFin AI Equity Analyst (Local Mode)
echo ===================================================

echo [1/3] Launching FastAPI Backend on port 8000...
start "LetsFin Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && .\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

echo [2/3] Launching Express Server on port 3000...
start "LetsFin Express Server" cmd /k "cd /d "%~dp0server" && node index.js"

echo [3/3] Launching React Vite Frontend on port 5173...
start "LetsFin React Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo All three services have been launched in separate windows!
echo - Frontend will be at: http://localhost:5173
echo - Express Server is at: http://localhost:3000
echo - FastAPI Backend is at: http://localhost:8000
echo ===================================================
pause

