@echo off
title P.H.O.E.N.I.X. - Build Windows Installer (.exe)
echo =========================================================
echo   Compiling P.H.O.E.N.I.X. Windows Setup (.exe) Installer
echo =========================================================

REM Check if Inno Setup is installed
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    echo Compiling with Inno Setup...
    %ISCC% "installer\phoenix_installer.iss"
    echo [SUCCESS] Installer generated at: installer\dist_installer\PHOENIX_Setup.exe
    pause
    exit /b
)

set ISCC_LOCAL="C:\Program Files\Inno Setup 6\ISCC.exe"
if exist %ISCC_LOCAL% (
    echo Compiling with Inno Setup...
    %ISCC_LOCAL% "installer\phoenix_installer.iss"
    echo [SUCCESS] Installer generated at: installer\dist_installer\PHOENIX_Setup.exe
    pause
    exit /b
)

echo [NOTE] Inno Setup compiler (ISCC.exe) was not found in standard paths.
echo You can download Inno Setup (free) from: https://jrsoftware.org/isdl.php
echo Once installed, double-click this file again or open 'installer\phoenix_installer.iss' in Inno Setup.
pause
