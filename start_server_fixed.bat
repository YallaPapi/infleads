@echo off
echo ===============================================
echo Starting R27 Infinite AI Leads Agent (FIXED)
echo ===============================================
echo.

REM Kill any existing Python processes
echo Cleaning up old processes...
powershell -Command "Get-Process python* 2>$null | Stop-Process -Force 2>$null"
timeout /t 2 /nobreak >nul

REM Clear Python cache
echo Clearing cache...
rd /s /q __pycache__ 2>nul
rd /s /q .pytest_cache 2>nul
rd /s /q instance 2>nul
del /s /q *.pyc 2>nul

REM Set Flask environment variables for development
echo Setting development environment...
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set TEMPLATES_AUTO_RELOAD=true
set SEND_FILE_MAX_AGE_DEFAULT=0

REM Start Flask
echo.
echo ===============================================
echo Server starting on http://localhost:5000
echo ===============================================
echo.
echo IMPORTANT: To ensure changes are reflected:
echo 1. Hard refresh browser: Ctrl+Shift+R
echo 2. Open DevTools (F12) and check "Disable cache" in Network tab
echo 3. Keep DevTools open while testing
echo.
echo Press Ctrl+C to stop the server
echo ===============================================
echo.

python app.py

pause