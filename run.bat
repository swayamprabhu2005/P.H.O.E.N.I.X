@echo off
title P.H.O.E.N.I.X. Desktop Assistant
echo =========================================================
echo   Starting P.H.O.E.N.I.X. Holographic Desktop Agent...
echo =========================================================
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b
)

REM Verify dependencies and install if missing
python -c "import pywebview, vosk, sounddevice, pyttsx3" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages for P.H.O.E.N.I.X...
    pip install pywebview pystray vosk sounddevice pyttsx3 pywin32 python-docx python-pptx pillow psutil
)

python app\main.py
if errorlevel 1 (
    echo.
    echo Application stopped. Press any key to exit.
    pause
)
