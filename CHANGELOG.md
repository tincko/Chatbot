# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-05

### 🎉 Lanzamiento Inicial

#### ✨ Agregado

**Sistema de Chat**
- Chat interactivo dual-LLM (psicólogo + paciente)
- Sugerencias de respuesta del modelo paciente
- Historial de conversación en tiempo real
- Soporte para múltiples modelos Ollama

**Gestión de Pacientes**
- Creación manual de perfiles de pacientes
- Generación automática de perfiles con IA
- Campos detallados: demográficos, médicos y psicológicos
- Persistencia en base de datos SQLite

**Sistema de Análisis**
- Análisis de interacciones con LLMs
- Chat interactivo con historial de sesiones
- Exportación de análisis a PDF
- Visualización de patrones terapéuticos

**Sistema RAG (Retrieval-Augmented Generation)**
- Carga de documentos de referencia
- Indexación con ChromaDB
- Búsqueda semántica en documentos
- Re-indexación configurable

**Generación Automática**
- Simulación completa de sesiones terapéuticas
- Control de número de turnos
- Configuración independiente de parámetros

**Persistencia de Datos**
- Migración completa a SQLite
- Almacenamiento de pacientes, interacciones y mensajes
- Sistema de respaldo y recuperación

**Interfaz de Usuario**
- Diseño moderno y responsivo
- Navegación por pestañas (Setup, Chat, History)
- Exportación de reportes a PDF
- Gestión de documentos RAG

#### 🏗️ Arquitectura

- Backend: FastAPI + SQLAlchemy + ChromaDB
- Frontend: React + Vite
- Base de datos: SQLite
- Modelos: Ollama (local)

#### 📚 Documentación

- README completo con guía de instalación
- Guía de contribución
- Licencia MIT
- Documentación de migración a SQLite

---

## [Unreleased]

### 🚀 Planificado

- [ ] Sistema de autenticación de usuarios
- [ ] Soporte multi-idioma
- [ ] Dashboard de estadísticas avanzadas
- [ ] Métricas de evaluación automática
- [ ] Exportación a múltiples formatos (CSV, JSON)
- [ ] Integración con APIs de LLM en la nube (opcional)
- [ ] Tests automatizados
- [ ] CI/CD con GitHub Actions

---

## Tipos de Cambios

- `✨ Agregado` - para nuevas características
- `🔧 Cambiado` - para cambios en funcionalidad existente
- `🐛 Corregido` - para corrección de bugs
- `⚠️ Deprecado` - para características que serán removidas
- `🗑️ Eliminado` - para características eliminadas
- `🔒 Seguridad` - en caso de vulnerabilidades
