#!/bin/bash

echo "============================================"
echo "  Sistema de Simulacion de Terapia Dual-LLM"
echo "============================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no esta instalado"
    echo "Por favor instala Python 3.8+ desde https://www.python.org/downloads/"
    exit 1
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js no esta instalado"
    echo "Por favor instala Node.js desde https://nodejs.org/"
    exit 1
fi

# Verificar Ollama
if ! command -v ollama &> /dev/null; then
    echo "[ADVERTENCIA] Ollama no esta instalado"
    echo "Por favor instala Ollama desde https://ollama.ai/"
    echo "La aplicacion necesita Ollama para funcionar."
    read -p "Presiona Enter para continuar..."
fi

echo "[1/4] Verificando dependencias de Python..."
cd web_app/backend

if [ ! -d "venv" ]; then
    echo "[INFO] Creando entorno virtual..."
    python3 -m venv venv
fi

echo "[INFO] Activando entorno virtual..."
source venv/bin/activate

echo "[INFO] Instalando/actualizando dependencias..."
pip install -q -r requirements.txt

echo ""
echo "[2/4] Verificando dependencias de Node.js..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "[INFO] Instalando dependencias de Node.js..."
    npm install
fi

echo ""
echo "[3/4] Iniciando Backend (Python)..."
cd ../backend

# Iniciar backend en segundo plano
source venv/bin/activate
python main.py &
BACKEND_PID=$!

echo "[INFO] Backend PID: $BACKEND_PID"
echo "[INFO] Esperando 3 segundos para que el backend inicie..."
sleep 3

echo ""
echo "[4/4] Iniciando Frontend (React)..."
cd ../frontend

# Iniciar frontend en segundo plano
npm run dev &
FRONTEND_PID=$!

echo "[INFO] Frontend PID: $FRONTEND_PID"

echo ""
echo "============================================"
echo "  Aplicacion iniciada correctamente!"
echo "============================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Abre tu navegador en: http://localhost:5173"
echo ""
echo "Para detener la aplicacion, presiona Ctrl+C"
echo ""

# Función para cleanup al salir
cleanup() {
    echo ""
    echo "Deteniendo aplicacion..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Aplicacion detenida."
    exit 0
}

# Capturar Ctrl+C
trap cleanup INT TERM

# Esperar a que el usuario detenga la aplicación
wait
