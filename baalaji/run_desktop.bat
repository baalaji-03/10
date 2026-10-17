@echo off
TITLE Baalaji Pharmacy Management System - Desktop Launcher
color 0B
echo ================================================================
echo        BAALAJI PHARMACY MANAGEMENT SYSTEM (DESKTOP)
echo ================================================================
echo.
echo Launching Electron Windows Desktop App...
echo.

:: Ensure Electron packages installed if needed
if not exist "desktop\node_modules\" (
    echo Installing Desktop App dependencies...
    cd desktop
    call npm.cmd install
    cd ..
)

:: Run Electron
call npx.cmd electron desktop
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo If Electron failed to start, run: npm.cmd install
    pause
)
