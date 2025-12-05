# ❓ Preguntas Frecuentes (FAQ)

## General

### ¿Qué es este proyecto?

Es una aplicación de simulación de terapia que utiliza dos modelos de lenguaje (LLMs) para ayudar a profesionales de la salud mental a practicar sus habilidades terapéuticas. Un modelo actúa como psicólogo y otro como paciente.

### ¿Es gratuito?

Sí, es completamente gratuito y de código abierto bajo la licencia MIT.

### ¿Necesito conexión a Internet?

Solo para la instalación inicial. Una vez configurado, funciona completamente offline usando modelos LLM locales con Ollama.

### ¿Puedo usar esto con pacientes reales?

**NO**. Esta es una herramienta de **práctica y entrenamiento únicamente**. No debe usarse para diagnóstico o tratamiento de pacientes reales. Los modelos de IA pueden generar respuestas incorrectas o inapropiadas.

## Instalación y Configuración

### ¿Qué requisitos de hardware necesito?

**Mínimo:**
- 8 GB RAM
- CPU de 4 núcleos
- 10 GB espacio en disco

**Recomendado:**
- 16 GB RAM
- CPU de 8 núcleos o GPU NVIDIA
- SSD con 20 GB libres

### ¿Qué modelos LLM debería usar?

Para empezar, recomendamos:
- **Llama 3.2 3B** - Rápido, ideal para hardware limitado
- **Qwen 2.5 7B** - Buen balance calidad/velocidad
- **Llama 3.1 8B** - Alta calidad

```bash
ollama pull llama3.2:3b
ollama pull qwen2.5:7b
```

### ¿Puedo usar modelos diferentes para psicólogo y paciente?

¡Sí! Puedes configurar modelos diferentes en la pestaña "Setup". Por ejemplo:
- Psicólogo: modelo más grande y preciso
- Paciente: modelo más rápido

### No puedo instalar Ollama, ¿hay alternativas?

Actualmente, el sistema requiere Ollama. En el futuro, planeamos agregar soporte para:
- APIs de OpenAI/Anthropic
- Otros servidores de LLM locales

## Uso de la Aplicación

### ¿Cómo inicio la aplicación?

**Método rápido (Windows):**
```bash
start_app.bat
```

**Método manual:**
```bash
# Terminal 1 - Backend
cd web_app/backend
python main.py

# Terminal 2 - Frontend
cd web_app/frontend
npm run dev
```

Luego abre `http://localhost:5173`

### ¿Cómo creo un perfil de paciente?

Dos opciones:

1. **Automático** (recomendado):
   - Ve a Setup → Patient Profile
   - Click en "Generate with AI"
   - Opcional: agrega guidance
   - Espera ~30 segundos
   - Revisa y guarda

2. **Manual**:
   - Completa todos los campos
   - Click en "Save Patients"

### Las respuestas del LLM son muy lentas, ¿es normal?

Sí, es normal para modelos locales. Factores que afectan la velocidad:
- Tamaño del modelo (7B es más lento que 3B)
- Hardware disponible
- Longitud del historial
- GPU vs CPU

**Soluciones:**
- Usa modelos más pequeños
- Reduce `max_tokens`
- Usa GPU si está disponible
- Cierra otras aplicaciones

### ¿Cómo funciona el sistema RAG?

El sistema RAG (Retrieval-Augmented Generation) permite:
1. Subir documentos (PDFs, TXT)
2. El sistema los divide en chunks y los indexa
3. Durante el chat, busca información relevante
4. La incluye en el contexto del LLM

**Para usar:**
- Ve a History → RAG Configuration
- Arrastra documentos
- Selecciona documentos en el chat
- El sistema los usará automáticamente

### ¿Puedo exportar las sesiones?

Sí, en la pestaña History:
- Selecciona interacción(es)
- Click en "Analyze with AI"
- Espera el análisis
- Click en "Download PDF Analysis"

## Solución de Problemas

### Error: "Connection refused" al iniciar

**Problema:** El backend no está corriendo o está en otro puerto.

**Solución:**
```bash
# Verifica que el backend esté corriendo
cd web_app/backend
python main.py

# Debería mostrar:
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### Error: "Model not found"

**Problema:** El modelo no está instalado en Ollama.

**Solución:**
```bash
# Lista modelos disponibles
ollama list

# Si falta, instala
ollama pull qwen2.5:7b
```

### Error: "Database locked"

**Problema:** Múltiples procesos intentan acceder a SQLite.

**Solución:**
- Cierra todas las instancias del backend
- Inicia solo una instancia
- Si persiste, elimina `chatbot.db` (perderás datos)

### Las sugerencias del paciente no aparecen

**Problema:** El modelo paciente no está configurado o hay un timeout.

**Solución:**
1. Verifica Setup → Patient Helper Model esté seleccionado
2. Verifica que el prompt del paciente esté configurado
3. Aumenta el timeout en el código si es necesario

### El análisis tarda demasiado o da timeout

**Problema:** El análisis procesa mucho texto.

**Solución:**
1. Reduce el número de interacciones seleccionadas
2. Usa un modelo más rápido
3. Reduce `max_tokens` del análisis
4. Simplifica el prompt de análisis

### ChromaDB error al subir documentos

**Problema:** Error en la indexación de documentos.

**Solución:**
```bash
# Limpia la base de datos vectorial
cd web_app
rm -rf chroma_db/  # Linux/Mac
# o
rmdir /s chroma_db  # Windows

# Reinicia el backend
```

## Datos y Privacidad

### ¿Dónde se guardan mis datos?

Todos los datos se guardan localmente en:
- **Base de datos**: `web_app/backend/chatbot.db`
- **Documentos**: `web_app/backend/documentos/`
- **ChromaDB**: `web_app/chroma_db/`

Ningún dato sale de tu computadora.

### ¿Puedo hacer backup de mis datos?

Sí, simplemente copia:
```bash
# Backup completo
cp web_app/backend/chatbot.db backup/
cp -r web_app/backend/documentos/ backup/
cp -r web_app/chroma_db/ backup/
```

### ¿Cómo borro todos los datos?

```bash
# Elimina la base de datos
rm web_app/backend/chatbot.db

# Elimina documentos
rm -rf web_app/backend/documentos/*

# Elimina ChromaDB
rm -rf web_app/chroma_db/*
```

La próxima vez que inicies, se crearán nuevas bases de datos vacías.

## Desarrollo y Contribución

### ¿Puedo contribuir al proyecto?

¡Sí! Lee `CONTRIBUTING.md` para las guías.

### ¿Dónde reporto bugs?

Abre un issue en GitHub con:
- Descripción del problema
- Pasos para reproducirlo
- Logs del backend y frontend
- Tu sistema operativo y versiones

### ¿Hay una roadmap?

Sí, revisa el archivo `CHANGELOG.md` sección "Unreleased" para ver las características planificadas.

### ¿Puedo solicitar nuevas características?

¡Por supuesto! Abre un issue con:
- Descripción de la característica
- Caso de uso
- Por qué sería útil

## Avanzado

### ¿Puedo cambiar el puerto del backend?

Sí, edita `web_app/backend/main.py`:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # Cambia port=8000 a tu puerto preferido
```

También actualiza el frontend para usar el nuevo puerto.

### ¿Puedo usar PostgreSQL en lugar de SQLite?

Sí, pero requiere modificaciones:
1. Instala `psycopg2`
2. Modifica `DATABASE_URL` en `database.py`
3. Actualiza las configuraciones de conexión

### ¿Cómo personalizo los prompts del sistema?

Ve a Setup → System Prompts y edita:
- Psychologist System Prompt
- Patient System Prompt

Estos se guardan y se usan en todas las conversaciones futuras.

### ¿Puedo agregar más campos a los perfiles de pacientes?

Sí, pero requiere cambios en:
1. `database.py` - Modelo Patient
2. `db_helpers.py` - Funciones CRUD
3. Frontend - Formulario de paciente

Consulta `ARCHITECTURE.md` para más detalles.

---

## ¿No encuentras tu pregunta?

- Revisa la [documentación completa](README.md)
- Revisa [issues existentes](https://github.com/tuusuario/proyecto/issues)
- Abre un [nuevo issue](https://github.com/tuusuario/proyecto/issues/new)

---

**Última actualización**: 2025-12-05
