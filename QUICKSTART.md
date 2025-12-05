# ⚡ Guía de Inicio Rápido

¿Quieres probar la aplicación **ahora mismo**? Sigue estos pasos.

## 📦 Prerrequisitos (5 minutos)

### 1. Instala Ollama
```bash
# Windows: Descarga desde https://ollama.ai/download/windows
# Mac: 
brew install ollama
# Linux:
curl https://ollama.ai/install.sh | sh
```

### 2. Descarga un modelo LLM
```bash
# Modelo ligero (recomendado para empezar)
ollama pull llama3.2:3b

# O modelo de calidad media
ollama pull qwen2.5:7b
```

### 3. Verifica Python y Node.js
```bash
python --version  # Debe ser 3.8+
node --version    # Debe ser 16+
```

Si no los tienes:
- **Python**: https://www.python.org/downloads/
- **Node.js**: https://nodejs.org/

## 🚀 Instalación (5 minutos)

### Opción A: Script Automático (Más Fácil)

**Windows:**
```bash
git clone https://github.com/tuusuario/chatbot-terapia.git
cd chatbot-terapia
start_app.bat
```

**Mac/Linux:**
```bash
git clone https://github.com/tuusuario/chatbot-terapia.git
cd chatbot-terapia
chmod +x start_app.sh
./start_app.sh
```

El script:
✅ Crea el entorno virtual de Python  
✅ Instala todas las dependencias  
✅ Inicia backend y frontend automáticamente

### Opción B: Manual

**1. Backend:**
```bash
cd web_app/backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

**2. Frontend (en otra terminal):**
```bash
cd web_app/frontend
npm install
npm run dev
```

## 🎮 Primer Uso (5 minutos)

### 1. Abre la aplicación
Navega a: **http://localhost:5173**

### 2. Configura los modelos (Pestaña "Setup")
- **Psychologist Model**: Selecciona `qwen2.5:7b` o el modelo que instalaste
- **Patient Helper Model**: Selecciona el mismo u otro modelo
- Click en "Load Default Prompts"

### 3. Genera un paciente
- Scroll down → "Patient Profile"
- Click en **"Generate with AI"**
- Espera ~30 segundos
- Revisa el perfil generado
- Click en **"Save Patients"**

### 4. Inicia una sesión (Pestaña "Chat")
- El psicólogo (IA) te saludará automáticamente
- Escribe tu respuesta como terapeuta
- Click en "Get Suggestion" si quieres una sugerencia del paciente
- Continúa la conversación
- Click en "Save Chat" cuando termines

### 5. Analiza la sesión (Pestaña "History")
- Verás tu sesión guardada
- Selecciónala con el checkbox
- Click en **"Analyze with AI"**
- Espera el análisis (~1 minuto)
- Lee el análisis generado
- Opcionalmente, exporta a PDF

## ✅ ¡Listo!

Ya tienes el sistema funcionando. Ahora puedes:

- 👥 Crear más pacientes
- 💬 Practicar diferentes escenarios terapéticos
- 📊 Analizar tus sesiones
- 📚 Subir documentos de referencia (RAG)
- 🤖 Generar sesiones automáticas

## 🆘 Problemas Comunes

### "Error: Connection refused"
**Solución**: El backend no está corriendo. Verifica que `python main.py` esté ejecutándose en otra terminal.

### "Model not found"
**Solución**: 
```bash
ollama pull qwen2.5:7b
```

### El LLM responde muy lento
**Solución**: 
- Usa un modelo más pequeño: `ollama pull llama3.2:3b`
- Reduce `max_tokens` en Setup (ej: 300)
- Cierra otras aplicaciones

### "Module not found: FastAPI"
**Solución**:
```bash
cd web_app/backend
# Activa el venv primero
pip install -r requirements.txt
```

## 📚 Siguiente Paso

Una vez que domines lo básico:

1. Lee el [README completo](README.md) para características avanzadas
2. Consulta [FAQ.md](FAQ.md) para preguntas comunes
3. Revisa [ARCHITECTURE.md](ARCHITECTURE.md) si quieres contribuir

## 💡 Tips

- **Modelos recomendados por hardware**:
  - 8GB RAM: `llama3.2:3b`
  - 16GB RAM: `qwen2.5:7b` o `llama3.1:8b`
  - 32GB+ RAM o GPU: `llama3.1:70b` o superior

- **Prompts más efectivos**:
  - Sé específico con el contexto del paciente
  - Incluye el enfoque terapéutico deseado (CBT, humanista, etc.)
  - Menciona objetivos de la sesión

- **RAG más útil**:
  - Sube guías clínicas relevantes
  - Incluye protocolos de tratamiento
  - Agrega literatura especializada

---

**¿Todo funcionando?** ¡Excelente! Ahora a practicar 🎯

**¿Problemas?** Consulta [FAQ.md](FAQ.md) o abre un issue en GitHub.
