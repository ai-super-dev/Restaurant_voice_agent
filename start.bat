@echo off
REM Quick start script for Windows
REM This script helps you start all services easily

echo ========================================
echo   Voice Agent Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please create .env from env.example and fill in your credentials:
    echo   copy env.example .env
    echo   notepad .env
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting webhook server...
echo.
start "Webhook Server" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python webhook_server.py"

timeout /t 2 /nobreak >nul

echo [2/3] Starting ngrok tunnel...
echo.
echo Make sure ngrok is installed from https://ngrok.com/
echo.
start "ngrok" cmd /k "ngrok http 8000"

timeout /t 3 /nobreak >nul

echo [3/3] Starting AI agent...
echo.
start "AI Agent" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python agent.py"

echo.
echo ========================================
echo   All services started!
echo ========================================
echo.
echo Three windows should have opened:
echo   1. Webhook Server (port 8000)
echo   2. ngrok (tunneling)  
echo   3. AI Agent (LiveKit)
echo.
echo Next steps:
echo   1. Copy the HTTPS URL from ngrok window
echo   2. Go to Twilio Console
echo   3. Configure webhook: https://YOUR-NGROK-URL/incoming-call
echo   4. Call your Twilio number to test!
echo.
echo Press any key to exit this window...
pause >nul

