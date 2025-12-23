@echo off
echo ============================================
echo   Sistema de Simulacion de Dual-LLM
echo ============================================
echo.

REM Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.8+ desde https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js no esta instalado o no esta en el PATH
    echo Por favor instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar Ollama
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ADVERTENCIA] Ollama no esta instalado o no esta en el PATH
    echo Por favor instala Ollama desde https://ollama.ai/
    echo La aplicacion necesita Ollama para funcionar.
    pause
)

echo [1/4] Verificando dependencias de Python...
cd web_app\backend
if not exist venv (
    echo [INFO] Creando entorno virtual...
    python -m venv venv
)

echo [INFO] Activando entorno virtual...
call venv\Scripts\activate

echo [INFO] Instalando/actualizando dependencias...
pip install -q -r requirements.txt

echo.
echo [2/4] Verificando dependencias de Node.js...
cd ..\frontend
if not exist node_modules (
    echo [INFO] Instalando dependencias de Node.js...
    call npm install
)

echo.
echo [3/4] Iniciando Backend (Python)...
cd ..\backend
start "LLM-Dual - Backend" cmd /k "call venv\Scripts\activate && python main.py"

echo [INFO] Esperando 10 segundos para que el backend inicie...
timeout /t 10 /nobreak >nul

echo.
echo [4/4] Iniciando Frontend (React)...
cd ..\frontend
start "LLM-Dual - Frontend" cmd /k "npm run dev"

echo.
echo ============================================
echo   Aplicacion iniciada correctamente!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Abre tu navegador en: http://localhost:5173
echo.
echo Para detener la aplicacion, cierra las ventanas del backend y frontend.
echo.
pause
