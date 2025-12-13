@echo off
echo ============================================
echo   Iniciando Backend en Modo Depuracion
echo ============================================
echo.
cd web_app\backend
call venv\Scripts\activate
python -u main.py
pause
