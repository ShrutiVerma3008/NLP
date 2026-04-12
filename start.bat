@echo off
echo Starting AI RIS Backend...
cd /d "%~dp0backend"
call venv\Scripts\activate
start "AI RIS Backend" python main.py
timeout /t 3 /nobreak >nul
echo Starting AI RIS Frontend...
cd /d "%~dp0frontend"
start "AI RIS Frontend" cmd /k "npm run dev"
echo.
echo Both servers starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause
