@echo off
title P.H.O.E.N.I.X. - Build Windows Installer (.exe)
echo =========================================================
echo   Compiling P.H.O.E.N.I.X. Windows Setup (.exe) Installer
echo =========================================================

REM Ensure working directory is project root
cd /d "%~dp0\.."

REM Check Inno Setup 7 and 6 installation paths
set ISCC=""

if exist "C:\Program Files\Inno Setup 7\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 7\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" (
    set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
) else (
    where iscc >nul 2>&1
    if not errorlevel 1 set ISCC=iscc
)

if not %ISCC%=="" (
    echo Compiling installer with Inno Setup: %ISCC%
    %ISCC% "installer\phoenix_installer.iss"
    if errorlevel 1 (
        echo.
        echo [ERROR] Inno Setup compilation failed!
        pause
        exit /b 1
    )
    echo.
    echo =========================================================
    echo [SUCCESS] PHOENIX_Setup.exe generated successfully!
    echo Location: installer\dist_installer\PHOENIX_Setup.exe
    echo =========================================================
    pause
    exit /b 0
)

echo [NOTE] Inno Setup compiler (ISCC.exe) was not found.
echo Please run the Inno Setup installer you downloaded, then double-click this script again.
pause
