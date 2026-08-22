@echo off
REM Local quickstart without Docker (SQLite)
REM Ports 8000/3000 are often blocked on Windows, so we use 8080/3001.
cd /d %~dp0backend
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
if not exist .env copy ..\.env.example .env
findstr /C:"PTN_NETWORK_ENABLED" .env >nul 2>&1
if errorlevel 1 (
  echo PTN_NETWORK_ENABLED=true>> .env
  echo PTN_NETWORK_GIT_URL=https://github.com/AmmarJamshed/pakistan-trust-network.git>> .env
)
set PTN_NETWORK_ENABLED=true
set PYTHONPATH=%CD%
.venv\Scripts\python -m scripts.seed
start "PTN API" cmd /c "set PTN_NETWORK_ENABLED=true&& .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8080"
cd /d %~dp0frontend
if not exist node_modules call npm install
if not exist .env.local echo NEXT_PUBLIC_API_URL=http://localhost:8080> .env.local
start "PTN Web" cmd /c "npx next dev -p 3001"
echo.
echo PTN Web:  http://localhost:3001
echo PTN API:  http://localhost:8080/api/docs
echo Network:  http://localhost:3001/run
echo Demo:     student@demo.ptn / DemoPass123!
