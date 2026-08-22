@echo off
REM Local quickstart without Docker (SQLite)
REM Ports 8000/3000 are often blocked or contested on Windows, so we use 8080/3001.
cd /d %~dp0backend
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
if not exist .env copy ..\.env.example .env
set PYTHONPATH=%CD%
.venv\Scripts\python -m scripts.seed
start "PTN API" cmd /c ".venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8080"
cd /d %~dp0frontend
if not exist node_modules call npm install
if not exist .env.local echo NEXT_PUBLIC_API_URL=http://localhost:8080> .env.local
start "PTN Web" cmd /c "npx next dev -p 3001"
echo.
echo PTN Web:  http://localhost:3001
echo PTN API:  http://localhost:8080/api/docs
echo Demo:     student@demo.ptn / DemoPass123!
