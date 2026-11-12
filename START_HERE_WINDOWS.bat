@echo off
setlocal enabledelayedexpansion
title Caliper: The Sewing & Calibration Atelier

cd /d "%~dp0"

echo ===================================================================
echo  Caliper: The Sewing & Calibration Atelier
echo  Universal Mechanical Sewing Machine Setup & Calibration Agent
echo ===================================================================
echo.

:: 1. Detect Python 3 on system
set "PY_CMD="
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

if "%PY_CMD%"=="" (
    echo [ERROR] Python 3 was not detected on your Windows system.
    echo Please install Python 3.10+ from https://www.python.org/downloads/windows/
    echo (Make sure to check "Add Python to PATH" during installation)
    echo.
    pause
    exit /b 1
)

:: 2. Setup isolated virtual environment in .venv
if not exist ".venv" (
    echo [Caliper] Creating isolated virtual environment in .venv...
    %PY_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create .venv virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Activate virtual environment
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate .venv environment.
    pause
    exit /b 1
)

:: 4. Install dependencies if marker is missing
if not exist ".venv\.deps_installed" (
    echo [Caliper] First-time setup: installing dependencies from requirements.txt...
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requirements from requirements.txt.
        pause
        exit /b 1
    )
    type nul > ".venv\.deps_installed"
    echo [Caliper] Dependencies successfully installed!
    echo.
)

:: 5. Open browser after short delay in background
echo [Caliper] Pre-loading 50-machine hardware database and launching browser...
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:7860"

:: 6. Start Caliper Web Application
echo.
echo ===================================================================
echo  Caliper Atelier is running at: http://127.0.0.1:7860
echo  (Keep this command prompt open. Press Ctrl+C to stop the server)
echo ===================================================================
echo.
python app.py

pause

