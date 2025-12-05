# 🧠 Sistema de Simulación de Terapia con Dual-LLM

Una aplicación web interactiva que utiliza dos modelos de lenguaje (LLMs) para simular sesiones terapéuticas, permitiendo a profesionales de la salud mental practicar y perfeccionar sus habilidades terapéuticas en un entorno seguro y controlado.

## 📋 Índice

- [Propósito](#-propósito)
- [Características Principales](#-características-principales)
- [Arquitectura](#️-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## 🎯 Propósito

Este sistema está diseñado para ayudar a psicólogos, psiquiatras y terapeutas a:

- **Practicar técnicas terapéuticas** en un entorno sin riesgos
- **Experimentar con diferentes enfoques** sin consecuencias para pacientes reales
- **Generar casos de estudio** automáticamente con perfiles de pacientes diversos
- **Analizar sesiones terapéuticas** utilizando IA para identificar patrones y áreas de mejora
- **Entrenar habilidades de comunicación** con pacientes simulados realistas

### ¿Cómo funciona?

El sistema utiliza **dos modelos de lenguaje que trabajan en conjunto**:

1. **Modelo Psicólogo**: Responde como un terapeuta profesional basado en las mejores prácticas
2. **Modelo Paciente**: Simula un paciente con características psicológicas específicas, ofreciendo sugerencias de respuesta al usuario (que actúa como terapeuta)

El usuario puede actuar como terapeuta, recibiendo sugerencias del "Modelo Paciente" sobre cómo podría responder un paciente real, permitiendo así practicar el diálogo terapéutico.

## ✨ Características Principales

### 🗣️ Chat Terapéutico Interactivo
- Conversación en tiempo real con asistencia de IA
- Sugerencias de respuestas del paciente simulado
- Historial completo de la conversación
- Soporte para múltiples modelos LLM locales (Ollama)

### 👥 Gestión de Pacientes
- Creación manual de perfiles de pacientes
- **Generación automática de perfiles** usando IA
- Perfiles detallados incluyendo:
  - Información demográfica
  - Historial médico y tratamientos
  - Rasgos de personalidad y estilo de comunicación
  - Fortalezas y dificultades
  - Notas del equipo terapéutico

### 📊 Análisis de Sesiones
- Análisis avanzado de interacciones usando LLMs
- Chat interactivo con el historial de sesiones
- Exportación de análisis en formato PDF
- Identificación de patrones terapéuticos
- Evaluación de técnicas utilizadas

### 📚 Sistema RAG (Retrieval-Augmented Generation)
- Carga de documentos de referencia (PDF, TXT, etc.)
- Indexación y búsqueda semántica
- Integración de conocimiento externo en las respuestas
- Re-indexación configurable de documentos

### 🤖 Generación Automática de Sesiones
- Simulación completa de sesiones terapéuticas
- Control del número de turnos de conversación
- Configuración independiente de parámetros para cada modelo
- Guardado automático en base de datos

### 💾 Persistencia de Datos
- Base de datos SQLite integrada
- Almacenamiento de:
  - Perfiles de pacientes
  - Historial de interacciones
  - Mensajes de cada sesión
  - Configuraciones de los modelos

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Chat Interface                                        │
│  - Patient Management                                    │
│  - Analysis Dashboard                                    │
│  - Document Upload                                       │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────────────────┐
│              Backend (FastAPI)                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Orchestrator (Dual-LLM Logic)              │ │
│  │  - Psychologist Model                              │ │
│  │  - Patient Model                                   │ │
│  │  - Suggestion Generation                           │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │           RAG Manager (ChromaDB)                   │ │
│  │  - Document Processing (Docling)                   │ │
│  │  - Semantic Search                                 │ │
│  │  - Vector Embeddings                               │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Database (SQLite)                         │ │
│  │  - Patients                                        │ │
│  │  - Interactions                                    │ │
│  │  - Messages                                        │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP API
┌──────────────────▼──────────────────────────────────────┐
│              Ollama (Local LLM Server)                   │
│  - Llama, Qwen, Mistral, etc.                           │
└─────────────────────────────────────────────────────────┘
```

## 📋 Requisitos Previos

### Software Requerido

- **Python 3.8+** ([Descargar](https://www.python.org/downloads/))
- **Node.js 16+** y **npm** ([Descargar](https://nodejs.org/))
- **Ollama** ([Descargar](https://ollama.ai/)) - Servidor de modelos LLM locales
- **Git** ([Descargar](https://git-scm.com/))

### Modelos LLM Recomendados

Descarga al menos uno de estos modelos usando Ollama:

```bash
# Modelos recomendados (elige según tu hardware)
ollama pull llama3.2:3b        # Ligero, rápido
ollama pull qwen2.5:7b         # Balance calidad/velocidad
ollama pull llama3.1:8b        # Alta calidad
ollama pull mistral:7b         # Alternativa excelente
```

### Requisitos de Hardware

- **Mínimo**: 8 GB RAM, CPU de 4 núcleos
- **Recomendado**: 16 GB RAM, CPU de 8 núcleos o GPU NVIDIA
- **Espacio en disco**: ~10 GB (modelos + datos)

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/chatbot-terapia.git
cd chatbot-terapia
```

### 2. Configurar el Backend

```bash
cd web_app/backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install sqlalchemy  # Dependencia adicional para la base de datos
```

### 3. Configurar el Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install
```

### 4. Iniciar Ollama

Asegúrate de que Ollama esté corriendo en tu sistema:

```bash
# Debería estar ejecutándose automáticamente después de la instalación
# Si no, inicia el servicio de Ollama según tu sistema operativo
```

Verifica que esté funcionando:

```bash
ollama list
```

## ⚙️ Configuración

### Configuración del Backend

El backend se conecta automáticamente a:
- **Ollama**: `http://localhost:11434`
- **SQLite**: Base de datos local en `web_app/backend/chatbot.db`
- **ChromaDB**: Almacenamiento vectorial en `web_app/chroma_db/`

No se requiere configuración adicional para un inicio rápido.

### Configuración del Frontend

El frontend se conecta por defecto a:
- **Backend API**: `http://localhost:8000`

Si necesitas cambiar esto, edita el archivo correspondiente en `web_app/frontend/src/`.

## 🎮 Uso

### Inicio Rápido (Opción Automatizada)

```bash
# Desde la raíz del proyecto
start_app.bat  # En Windows
# O manualmente (ver abajo)
```

### Inicio Manual

#### 1. Iniciar el Backend

```bash
cd web_app/backend
# Asegúrate de que el entorno virtual esté activado
python main.py
```

El backend estará disponible en: `http://localhost:8000`

#### 2. Iniciar el Frontend

En otra terminal:

```bash
cd web_app/frontend
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

#### 3. Abrir la Aplicación

Navega a `http://localhost:5173` en tu navegador.

### Flujo de Trabajo Típico

1. **Configurar Modelos** (Pestaña "Setup")
   - Selecciona los modelos LLM para psicólogo y paciente
   - Configura los prompts del sistema
   - Ajusta parámetros de generación

2. **Crear/Generar Paciente** (Pestaña "Setup")
   - Genera un perfil automáticamente con IA
   - O crea uno manualmente
   - Guarda el perfil

3. **Sesión Terapéutica** (Pestaña "Chat")
   - El psicólogo (IA) inicia la conversación
   - Tú respondes como terapeuta
   - Opcionalmente, usa las sugerencias del modelo paciente
   - Guarda la sesión cuando termines

4. **Analizar Sesiones** (Pestaña "History")
   - Revisa sesiones anteriores
   - Realiza análisis con IA
   - Chatea con el historial
   - Exporta reportes en PDF

## 📁 Estructura del Proyecto

```
chatbot-terapia/
├── web_app/
│   ├── backend/
│   │   ├── main.py                 # API FastAPI principal
│   │   ├── orchestrator.py         # Lógica de dual-LLM
│   │   ├── rag_manager.py          # Sistema RAG
│   │   ├── database.py             # Modelos SQLAlchemy
│   │   ├── db_helpers.py           # Funciones CRUD
│   │   ├── requirements.txt        # Dependencias Python
│   │   ├── chatbot.db             # Base de datos SQLite
│   │   ├── dialogos/              # Interacciones guardadas (legacy)
│   │   └── documentos/            # Documentos RAG
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx            # Componente principal
│   │   │   ├── index.css          # Estilos globales
│   │   │   └── main.jsx           # Punto de entrada
│   │   ├── package.json           # Dependencias Node
│   │   └── vite.config.js         # Configuración Vite
│   └── chroma_db/                 # Base de datos vectorial
├── README.md                       # Este archivo
└── start_app.bat                   # Script de inicio rápido
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **SQLite** - Base de datos relacional embebida
- **ChromaDB** - Base de datos vectorial para RAG
- **Sentence Transformers** - Embeddings semánticos
- **Docling** - Procesamiento de documentos
- **Uvicorn** - Servidor ASGI

### Frontend
- **React** - Biblioteca de UI
- **Vite** - Build tool y dev server
- **Lucide React** - Iconos
- **React Markdown** - Renderizado de markdown
- **jsPDF** - Generación de PDFs
- **html2canvas** - Captura de pantalla a PDF

### IA/ML
- **Ollama** - Servidor de LLMs locales
- **Modelos LLM** - Llama, Qwen, Mistral, etc.

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Áreas de Mejora

- [ ] Soporte para más tipos de documentos
- [ ] Métricas de evaluación de sesiones
- [ ] Sistema de autenticación de usuarios
- [ ] Exportación de datos en múltiples formatos
- [ ] Integración con APIs de LLM en la nube (opcional)
- [ ] Modo multi-idioma
- [ ] Dashboard de estadísticas avanzadas

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la [Licencia MIT](LICENSE).

---

## 📞 Soporte y Contacto

Si tienes preguntas o problemas:

1. **Revisa la documentación** en este README
2. **Abre un issue** en GitHub con detalles del problema
3. **Consulta los logs** del backend y frontend para debugging

## 🎓 Disclaimer

Esta aplicación es una herramienta de **práctica y entrenamiento**. No debe utilizarse como:
- Sustituto de supervisión profesional real
- Herramienta de diagnóstico clínico
- Sistema para tratamiento de pacientes reales

Los modelos de IA pueden generar respuestas incorrectas o inapropiadas. Siempre usa tu juicio profesional.

---

**Desarrollado con ❤️ para mejorar la formación en salud mental**
