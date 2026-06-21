@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  Factory Management System — Backend Startup Script (Windows)
REM  Run from: d:\SOP Manager\backend\
REM ─────────────────────────────────────────────────────────────────────────────

echo [1/4] Checking virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
pip install -r requirements.txt --quiet

echo [3/4] Checking .env file...
if not exist ".env" (
    echo WARNING: .env not found. Copying from .env.example...
    copy .env.example .env
    echo Please edit .env with your database credentials before continuing.
    pause
)

echo [4/4] Starting FastAPI server...
echo  - API:    http://127.0.0.1:8000
echo  - Docs:   http://127.0.0.1:8000/api/docs
echo  - Health: http://127.0.0.1:8000/health
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
