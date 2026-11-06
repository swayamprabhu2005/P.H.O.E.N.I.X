@echo off
title P.H.O.E.N.I.X. Desktop Assistant
cd /d "%~dp0"

where pythonw >nul 2>&1
if not errorlevel 1 (
    start "" pythonw app\main.py
    exit /b
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b
)

start "" python app\main.py
exit /b
