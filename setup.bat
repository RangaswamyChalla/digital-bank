@echo off
REM Digital Bank Project Startup Script

echo ========================================
echo Digital Bank - Project Setup
echo ========================================
echo.

REM Check if backend dependencies are installed
echo [1] Installing Backend Dependencies...
cd backend
pip install -r requirements.txt
cd ..
echo ✓ Backend dependencies installed

echo.

REM Check if frontend dependencies are installed
echo [2] Installing Frontend Dependencies...
cd frontend
call npm install
cd ..
echo ✓ Frontend dependencies installed

echo.

echo ========================================
echo Setup Complete! Your options:
echo ========================================
echo.
echo Option A - Run Both Services Separately:
echo   Terminal 1: cd backend && python run.py
echo   Terminal 2: cd frontend && npm run dev
echo.
echo Option B - Use Docker (Full Stack):
echo   docker-compose up --build
echo.
echo Option C - Run Backend Only:
echo   cd backend && python run.py
echo.
echo ========================================
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ========================================
echo.
