# Start all 3 LetsFin services in separate terminal windows

$root = $PSScriptRoot

Write-Host "Starting LetsFin AI Equity Analyst..." -ForegroundColor Cyan

# 1. Backend
Start-Process wt -ArgumentList "-w 0 new-tab --title `"Backend`" -d `"$root\backend`" powershell -NoExit -Command `".\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`"" -ErrorAction SilentlyContinue
if (-not $?) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$root\backend`"; .\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
}

# 2. Server
Start-Process wt -ArgumentList "-w 0 new-tab --title `"Server`" -d `"$root\server`" powershell -NoExit -Command `"node index.js`"" -ErrorAction SilentlyContinue
if (-not $?) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$root\server`"; node index.js"
}

# 3. Frontend
Start-Process wt -ArgumentList "-w 0 new-tab --title `"Frontend`" -d `"$root\frontend`" powershell -NoExit -Command `"npm run dev`"" -ErrorAction SilentlyContinue
if (-not $?) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$root\frontend`"; npm run dev"
}

Write-Host "Services started! Open http://localhost:5173 in your browser." -ForegroundColor Green

