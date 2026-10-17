@echo off
TITLE Build Baalaji Pharmacy Windows Executable (.exe)
color 0E
echo ================================================================
echo       BUILDING STANDALONE WINDOWS INSTALLER (.EXE)
echo ================================================================
echo.
echo Packaging Electron Desktop Application with electron-builder...
echo.

cd desktop
call npm.cmd install
call npm.cmd run build:win

echo.
echo ================================================================
echo Build process completed! Look in desktop\dist\ for .exe installer.
echo ================================================================
pause
