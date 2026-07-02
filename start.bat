@echo off
title Right Click AI
echo.
echo  ==============================
echo   Right Click AI - Starting...
echo  ==============================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    exit /b 1
)

:: Install Python dependencies (first run)
if not exist "backend\venv" (
    echo [Setup] Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
    echo [Setup] Python dependencies installed!
) else (
    call backend\venv\Scripts\activate
)

:: Install Node dependencies (first run)
if not exist "electron\node_modules" (
    echo [Setup] Installing Electron dependencies...
    cd electron
    npm install
    cd ..
    echo [Setup] Electron dependencies installed!
)

echo.
echo [Starting] Electron App...
cd electron
npx electron .
cd ..

echo.
echo [Stopped] Right Click AI has been closed.
