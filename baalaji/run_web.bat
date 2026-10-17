@echo off
TITLE Baalaji Pharmacy Management System - Web Server
color 0A
echo ================================================================
echo           BAALAJI PHARMACY MANAGEMENT SYSTEM (WEB)
echo ================================================================
echo.
echo Starting FastAPI Backend Server on http://127.0.0.1:8000 ...
echo.

:: Launch browser in 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start Uvicorn Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
