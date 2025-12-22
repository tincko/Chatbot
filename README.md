# 🏥 Sistema de Entrenamiento para Asistentes en Salud Renal (Dual-LLM)

Una plataforma interactiva avanzada diseñada para entrenar y evaluar "Asistentes en Salud Renal" utilizando Inteligencia Artificial. El sistema emplea una arquitectura Dual-LLM donde un modelo actúa como el **Asistente** (utilizando el modelo conductual COM-B) y otro simula ser un **Paciente de Trasplante Renal** con características realistas.

## 📋 Índice

- [Propósito](#-propósito)
- [Novedades y Cambios Recientes](#-novedades-y-cambios-recientes)
- [Características Principales](#-características-principales)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías](#-tecnologías)

## 🎯 Propósito

Este sistema permite a profesionales de la salud y desarrolladores:

- **Entrenar Asistentes Virtuales** especializados en el seguimiento de pacientes trasplantados.
- **Simular Escenarios de Adherencia**: Evaluar cómo el asistente maneja situaciones de olvido de medicación (Tacrolimus, MMF, etc.) o barreras emocionales.
- **Validar el Modelo COM-B**: Observar el razonamiento interno del asistente (Capacidad, Oportunidad, Motivación) antes de cada respuesta.
- **Probar Consistencia Temporal**: Simular el paso de días para verificar si el paciente (IA) recuerda compromisos o cambios en su rutina.

## 🚀 Novedades y Cambios Recientes

Esta versión ha evolucionado de un simulador genérico de psicología a una herramienta especializada en **Salud Renal**:

- **🩺 Especialización Renal**: Los perfiles de pacientes generados incluyen automáticamente detalles de trasplantes, medicación inmunosupresora (Tacrolimus, Prednisona, etc.) y contextos sociales específicos.
- **🧠 Razonamiento Visible (`<think>`)**: El asistente ahora "piensa" antes de hablar. Se puede ver su análisis interno basado en el modelo COM-B para decidir la mejor estrategia de intervención.
- **📅 Simulación de "Nuevo Día"**: Nueva funcionalidad para avanzar el tiempo arbitrariamente (ej. "Pasó un día"). El modelo paciente actualiza su estado y reporta si tomó o no la medicación en ese lapso.
- **👤 Modo Solitario**: Opción para interactuar directamente con el Asistente Renal sin la mediación del modelo Paciente (para pruebas manuales rápidas).

## ✨ Características Principales

### 🗣️ Simulación Dual-LLM
- **Modelo Asistente**: Instruido para ser empático, breve y usar "micro-nudges" conductuales.
- **Modelo Paciente**: Simula personalidad, adherencia irregular y respuestas emocionales coherentes con un paciente crónico.
- **Sugerencias Automáticas**: El sistema propone qué diría el paciente, permitiendo al usuario aceptar o modificar la respuesta.

### 👥 Gestión de Pacientes Renales
- **Generación AI de Perfiles**: Crea pacientes sintéticos con datos demográficos, régimen de medicación y barreras de adherencia (olvido, coste, soledad).
- **Persistencia y Edición**: Guarda perfiles y ajusta parámetros como "Nivel Educativo" o "Idiosincrasia" (ej. adaptado a pacientes de Uruguay/Latam).

### 📊 Análisis Clínico
- **Dashboard de Historia**: Revisa sesiones anteriores.
- **Evaluación Supervisada**: Un tercer modelo (Supervisor) analiza las transcripciones buscando empatía, claridad y uso correcto del modelo conductual.
- **RAG (Retrieval-Augmented Generation)**: Carga guías clínicas (PDF) para que el asistente y el analista tengan contexto médico actualizado.

### ⏱️ Control Temporal
- **Botón "Simular Nuevo Día"**: Introduce eventos narrativos (ej. "El paciente tuvo una cena familiar y se olvidó la dosis nocturna") para forzar al asistente a reaccionar ante la no-adherencia.

## 🏗️ Arquitectura

```mermaid
graph TD
    Client[Frontend (React/Vite)] <--> API[Backend (FastAPI)]
    
    subgraph Backend Services
        API <--> Orch[Orquestador Dual-LLM]
        API <--> DB[(SQLite - Pacientes/Logs)]
        API <--> VectorDB[(ChromaDB - RAG)]
    end
    
    subgraph AI Models (Local/Remote)
        Orch <--> LLM_Asst[Modelo Asistente (Mental-LLaMA)]
        Orch <--> LLM_Pat[Modelo Paciente (GPT-OSS / Llama)]
    end
```

## 📋 Requisitos Previos

1. **Python 3.8+**
2. **Node.js 16+** y NPM
3. **Servidor LLM Compatible con OpenAI API**:
   - Se recomienda **LM Studio** o **Ollama**.
   - Por defecto, el orquestador busca el servidor en `http://127.0.0.1:1234/v1/chat/completions`.
   - *Nota: Si usas Ollama estándar en el puerto 11434, asegúrate de configurar la URL o usar un proxy.*

## 💾 Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <repo-url>
   cd Chatbot
   ```

2. **Backend (Python)**:
   ```bash
   cd web_app/backend
   python -m venv venv
   # Activar: venv\Scripts\activate (Windows) o source venv/bin/activate (Linux/Mac)
   pip install -r requirements.txt
   ```

3. **Frontend (React)**:
   ```bash
   cd web_app/frontend
   npm install
   ```

4. **Configurar Modelos**:
   - Asegúrate de tener cargados los modelos en tu servidor local (LM Studio/Ollama).
   - Modelos sugeridos: `Llama-3.1-8B-Instruct` o fine-tunes médicos.

## 🎮 Uso

### Inicio Rápido

Ejecuta el script automático en Windows:
```bash
start_app.bat
```
Esto iniciará backend (puerto 8000) y frontend (puerto 5173).

### Flujo de Trabajo Típico

1. **Setup**: Ve a la pestaña **Setup**. Genera un **Nuevo Paciente** con IA o crea uno manualmente. Guarda el perfil.
2. **Selección**: Elige los modelos LLM para "Chatbot" (Asistente) y "Patient" (Paciente).
3. **Chat**: Ve a la pestaña **Chat**.
   - El Asistente iniciará la conversación.
   - Presiona "Generar Respuesta Paciente" para ver qué diría el paciente simulado.
   - Observa el bloque `<think>` para entender el razonamiento del asistente.
4. **Simular Tiempo**: Si quieres probar adherencia, usa el botón **"Simular Nuevo Día"**. Describe una situación (opcional) y observa cómo el paciente reporta su comportamiento del día anterior.
5. **Historia y Análisis**: Ve a **History** para revisar chats pasados o pedir un análisis clínico automático de la sesión.

## 📁 Estructura del Proyecto

- `web_app/backend/orchestrator.py`: Corazón del sistema. Maneja la lógica de turnos, prompts del sistema y limpieza de tags `<think>`.
- `web_app/backend/rag_manager.py`: Gestión de documentos PDF y búsqueda vectorial.
- `web_app/frontend/src/App.jsx`: Interfaz principal. Contiene la lógica de estado del chat y configuración.
- `web_app/frontend/src/index.css`: Estilos modernos con Tailwind/CSS vainilla.

## 🛠️ Tecnologías

- **Frontend**: React, Vite, Lucide Icons, React Markdown.
- **Backend**: FastAPI, SQLAlchemy, Uvicorn.
- **Datos**: SQLite (Relacional), ChromaDB (Vectorial).
- **IA**: Integración agnóstica (OpenAI format) para modelos locales.

---
**Desarrollado para la investigación en Salud Digital y Adherencia Terapéutica.**
