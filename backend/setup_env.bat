@echo off
echo ================================================
echo  AI RIS Backend — Environment Setup
echo ================================================

REM Step 1: Create virtual environment
echo [1/4] Creating virtual environment...
python -m venv venv

REM Step 2: Activate it
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Step 3: Upgrade pip to avoid old-resolver issues
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

REM Step 4: Install all dependencies
echo [4/4] Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo ================================================
echo  Done! To start the backend:
echo    venv\Scripts\activate
echo    python main.py
echo ================================================
pause
