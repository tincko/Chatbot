# 🏛️ Arquitectura Técnica

Documentación técnica detallada del sistema de simulación dual-LLM.

## 📐 Vista General de la Arquitectura

```
┌─────────────────── CAPA DE PRESENTACIÓN ──────────────────┐
│                                                            │
│  React Frontend (Port 5173)                               │
│  ├── App.jsx (Main Component)                            │
│  ├── Components/                                          │
│  │   ├── ChatView                                         │
│  │   ├── SetupView                                        │
│  │   └── HistoryView                                      │
│  └── API Client (fetch/axios)                            │
│                                                            │
└────────────────────────┬───────────────────────────────────┘
                         │ HTTP REST API
┌────────────────────────▼───────────────────────────────────┐
│                                                            │
│  FastAPI Backend (Port 8000)                              │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ API Endpoints                                        │ │
│  │ ├── /api/chat          - Chat con psicólogo        │ │
│  │ ├── /api/suggest       - Sugerencias del paciente  │ │
│  │ ├── /api/patients      - CRUD pacientes            │ │
│  │ ├── /api/interactions  - CRUD interacciones        │ │
│  │ ├── /api/analyze_*     - Análisis de sesiones      │ │
│  │ └── /api/documents     - Gestión RAG               │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Business Logic Layer                                │ │
│  │                                                      │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │ DualLLMOrchestrator                          │  │ │
│  │  │ - chat_psychologist()                        │  │ │
│  │  │ - generate_suggestion_only()                 │  │ │
│  │  │ - simulate_interaction()                     │  │ │
│  │  │ - analyze_interactions()                     │  │ │
│  │  │ - chat_analysis()                            │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  │                                                      │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │ RAGManager                                   │  │ │
│  │  │ - add_document()                             │  │ │
│  │  │ - query()                                    │  │ │
│  │  │ - delete_document()                          │  │ │
│  │  │ - clear_collection()                         │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Data Access Layer                                   │ │
│  │                                                      │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │ db_helpers.py                                │  │ │
│  │  │ - get_all_patients()                         │  │ │
│  │  │ - create_or_update_patients()                │  │ │
│  │  │ - save_interaction()                         │  │ │
│  │  │ - get_all_interactions()                     │  │ │
│  │  │ - get_interaction_by_filename()              │  │ │
│  │  │ - get_interactions_by_filenames()            │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────┬───────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐
    │ SQLite  │   │ ChromaDB │   │  Ollama  │
    │         │   │          │   │          │
    │ chatbot │   │ Vector   │   │ LLM API  │
    │   .db   │   │ Embeddings│   │:11434    │
    └─────────┘   └──────────┘   └──────────┘
```

## 🗄️ Modelo de Datos (SQLite)

### Tablas Principales

#### **patients**
```sql
CREATE TABLE patients (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    edad INTEGER,
    tipo_trasplante TEXT,
    medicacion TEXT,
    adherencia_previa TEXT,
    contexto TEXT,
    nivel_educativo TEXT,
    estilo_comunicacion TEXT,
    fortalezas TEXT,
    dificultades TEXT,
    notas_equipo TEXT,
    idiosincrasia TEXT,
    preferred_patient_model TEXT,
    last_interaction_file TEXT,
    last_interaction_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### **interactions**
```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    patient_id TEXT,
    chatbot_model TEXT,
    patient_model TEXT,
    psychologist_system_prompt TEXT,
    patient_system_prompt TEXT,
    psychologist_params JSON,
    patient_params JSON,
    filename TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);
```

#### **messages**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id INTEGER NOT NULL,
    order INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    suggested_reply_used BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interaction_id) REFERENCES interactions(id) ON DELETE CASCADE
);
```

### Relaciones

```
patients (1) ──── (*) interactions
                      │
                      └─── (*) messages
```

## 🔄 Flujo de Datos Principal

### 1. Chat Terapéutico

```
Usuario escribe mensaje
    │
    ▼
Frontend → POST /api/chat
    │
    ▼
Backend recibe ChatRequest
    │
    ├─→ RAGManager.query() [si hay documentos]
    │   └─→ ChromaDB busca contexto relevante
    │
    ├─→ DualLLMOrchestrator.chat_psychologist()
    │   └─→ Ollama API (modelo psicólogo)
    │       └─→ Genera respuesta terapéutica
    │
    ▼
Frontend recibe respuesta
    │
    ▼
Usuario solicita sugerencia
    │
    ▼
Frontend → POST /api/suggest
    │
    ▼
DualLLMOrchestrator.generate_suggestion_only()
    └─→ Ollama API (modelo paciente)
        └─→ Genera sugerencia de respuesta
    │
    ▼
Frontend muestra sugerencia
    │
    ▼
Usuario guarda interacción
    │
    ▼
Frontend → POST /api/save_interaction
    │
    ▼
db_helpers.save_interaction()
    └─→ SQLite guarda en interactions + messages
```

### 2. Análisis de Sesiones

```
Usuario selecciona interacciones
    │
    ▼
Frontend → POST /api/analyze_interactions
    │
    ▼
db_helpers.get_interactions_by_filenames()
    │
    ▼
SQLite retorna datos de interacciones
    │
    ▼
Orchestrator formatea contexto
    │
    ├─→ Incluye documentos RAG (opcional)
    │   └─→ Docling procesa PDFs
    │
    └─→ Ollama API genera análisis
    │
    ▼
Frontend muestra análisis
```

## 🧩 Componentes Clave

### Backend

#### **orchestrator.py**
Orquesta la interacción entre los dos modelos LLM.

```python
class DualLLMOrchestrator:
    def chat_psychologist(self, model, history, message, ...):
        """Genera respuesta del psicólogo"""
        
    def generate_suggestion_only(self, model, history, ...):
        """Genera sugerencia para el usuario (como paciente)"""
        
    def simulate_interaction(self, ...):
        """Simula una sesión completa automáticamente"""
        
    def analyze_interactions(self, model, context, prompt, ...):
        """Analiza interacciones guardadas"""
```

#### **rag_manager.py**
Gestiona el sistema de recuperación aumentada.

```python
class RAGManager:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("documents")
        self.doc_converter = DocumentConverter()
        
    def add_document(self, filename, filepath, chunk_size, overlap):
        """Indexa un documento en ChromaDB"""
        
    def query(self, query_text, n_results, filter_filenames):
        """Busca chunks relevantes en los documentos"""
```

#### **database.py**
Define los modelos SQLAlchemy.

```python
class Patient(Base):
    __tablename__ = "patients"
    # ... campos

class Interaction(Base):
    __tablename__ = "interactions"
    patient = relationship("Patient", back_populates="interactions")
    messages = relationship("Message", back_populates="interaction", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    interaction = relationship("Interaction", back_populates="messages")
```

### Frontend

#### **App.jsx**
Componente raíz que maneja la navegación y el estado global.

```javascript
function App() {
  const [view, setView] = useState('chat');
  const [patients, setPatients] = useState([]);
  const [models, setModels] = useState([]);
  // ... más estado
  
  // Vistas: 'setup', 'chat', 'history'
}
```

## 🔐 Seguridad

### Consideraciones Actuales

- ✅ CORS habilitado para desarrollo local
- ✅ Validación de datos con Pydantic
- ✅ Sanitización de nombres de archivo
- ⚠️ Sin autenticación (uso local/individual)
- ⚠️ Sin encriptación de datos sensibles

### Recomendaciones para Producción

- [ ] Implementar autenticación JWT
- [ ] Habilitar HTTPS
- [ ] Encriptar datos sensibles en BD
- [ ] Rate limiting en endpoints
- [ ] Validación de archivos subidos
- [ ] CORS restrictivo

## 📊 Performance

### Optimizaciones Implementadas

- **Frontend**: Build optimizado con Vite
- **Backend**: Async/await para operaciones I/O
- **Base de datos**: Índices en campos frecuentes
- **RAG**: Chunking estratégico de documentos

### Limitaciones Conocidas

- LLMs locales pueden ser lentos (depende del hardware)
- Documentos muy grandes pueden tardar en indexarse
- ChromaDB en memoria (no persistente por defecto)

## 🧪 Testing

### Áreas a Cubrir

- [ ] Unit tests para funciones de `db_helpers`
- [ ] Integration tests para endpoints API
- [ ] E2E tests para flujos principales
- [ ] Tests de carga para LLM endpoints

## 📈 Escalabilidad

### Limitaciones Actuales

- SQLite (bueno para 1 usuario, limitado para múltiples)
- Ollama local (requiere hardware potente)
- Sin cache de respuestas LLM

### Mejoras Futuras

- Migrar a PostgreSQL para multi-usuario
- Implementar queue system (Celery) para tareas largas
- Cache de embeddings y respuestas frecuentes
- Soporte para LLM en la nube como fallback

---

**Última actualización**: 2025-12-05
