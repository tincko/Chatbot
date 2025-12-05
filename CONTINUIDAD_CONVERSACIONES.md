# Continuidad de Conversaciones con Pacientes

## Descripción General

Esta funcionalidad permite que cada paciente tenga:
1. **Modelo LLM asociado**: Cada perfil de paciente puede tener su propio modelo de IA preferido.
2. **Historial persistente**: Las conversaciones se retoman automáticamente desde donde quedaron.

---

## Campos Agregados al Perfil de Paciente

### `preferred_patient_model` (string, opcional)
- **Propósito**: Define el modelo de IA específico que se usará para este paciente.
- **Valor por defecto**: Si está vacío o no está definido, se usa el modelo configurado globalmente.
- **Ejemplo**: `"mental_llama3.1-8b-mix-sft"`

### `last_interaction_file` (string, opcional)
- **Propósito**: Guarda el nombre del archivo JSON de la última interacción con este paciente.
- **Valor por defecto**: Vacío (paciente sin historial previo).
- **Ejemplo**: `"2025-12-04_14-32-21_Carlos_S.json"`

---

## Cómo Funciona

### 1. Selección de Paciente
Al hacer clic en **"Usar"** en la tabla de pacientes:
- Se carga el modelo preferido del paciente (si tiene uno configurado).
- Se busca y carga automáticamente el archivo de su última interacción.
- El historial de mensajes se carga en el chat.
- El paciente puede continuar la conversación desde donde quedó.

### 2. Guardado de Interacción
Al hacer clic en **"Guardar Interacción"** o generar un auto-chat:
- La interacción se guarda en un archivo JSON en `/dialogos/`.
- El nombre del archivo se actualiza en `last_interaction_file` del perfil del paciente.
- La próxima vez que se seleccione este paciente, se cargará automáticamente.

### 3. Indicador Visual
En la tabla de pacientes:
- Los pacientes con historial previo muestran un ícono verde 💬 junto a su nombre.
- Esto permite identificar rápidamente qué pacientes tienen conversaciones guardadas.

---

## Interfaz de Usuario

### Formulario de Paciente
Se agregó un nuevo campo:
- **"Modelo Preferido (Paciente)"**: Dropdown para seleccionar el modelo.
- Opción por defecto: "Usar configuración global"
- Lista de modelos disponibles cargada dinámicamente del servidor.

### Tabla de Pacientes
- Columna "Nombre" ahora incluye el ícono 💬 para pacientes con historial.
- Tooltip: "Tiene historial previo"

---

## Flujo Técnico

### Frontend (`App.jsx`)

#### `selectPatient(patient)`
```javascript
// 1. Carga el modelo preferido del paciente
const patientModel = patient.preferred_patient_model || config.patient_model;

// 2. Si existe last_interaction_file, carga el historial
if (patient.last_interaction_file) {
    const res = await fetch(`http://localhost:8000/api/interactions/${patient.last_interaction_file}`);
    const data = await res.json();
    setMessages(data.messages);
}
```

#### `saveInteraction()`
```javascript
// Al guardar, actualiza last_interaction_file en el perfil
const updatedPatient = { ...patient, last_interaction_file: data.filename };
setPatients(updatedPatients);
await savePatientsToBackend(updatedPatients);
```

### Backend (`main.py`)
- **Endpoint**: `GET /api/interactions/{filename}`
- Retorna el contenido completo del archivo JSON de interacción.
- Incluye: `config`, `messages`, `timestamp`

---

## Limitaciones y Consideraciones

### 1. Límite de Contexto
Los modelos LLM tienen un límite de tokens de contexto:
- **Problema**: Si el historial es muy largo (muchas sesiones acumuladas), puede exceder el límite.
- **Solución futura**: Implementar resumen automático del historial o usar solo las últimas N interacciones.

### 2. Continuidad vs Nueva Sesión
Actualmente:
- Al seleccionar un paciente, **siempre** se carga el historial si existe.
- No hay opción para "comenzar una nueva conversación fresca".
- **Solución futura**: Agregar un botón "Nueva Conversación" que ignore el historial.

### 3. Gestión de Archivos
- Los archivos de interacción se acumulan en `/dialogos/`.
- No hay limpieza automática de archivos antiguos.
- **Solución futura**: Implementar archivado o eliminación de interacciones antiguas.

---

## Ejemplos de Uso

### Caso 1: Paciente Nuevo
1. Crear paciente "María López"
2. Opcionalmente seleccionar un modelo preferido (ej: `mental_llama3.1-8b-mix-sft`)
3. Hacer clic en "Usar" → Se inicia chat vacío
4. Conversar y guardar interacción
5. **Resultado**: `María López` ahora tiene 💬 en su nombre

### Caso 2: Continuación de Conversación
1. Seleccionar "María López" (que ya tiene 💬)
2. **Automático**: Se cargan los mensajes previos
3. Iniciar sesión → El chat muestra el historial
4. Continuar la conversación desde donde quedó
5. Guardar → Se actualiza `last_interaction_file` con la nueva sesión

### Caso 3: Múltiples Pacientes con Diferentes Modelos
- **Carlos S.**: usa `deepseek/deepseek-r1-0528-qwen3-8b`
- **Ana López**: usa `mental_llama3.1-8b-mix-sft`
- **Juan Gómez**: usa configuración global

Al seleccionar cada paciente, el sistema automáticamente:
- Cambia al modelo específico del paciente
- Carga su historial único
- Adapta la conversación a su contexto

---

## Mantenimiento de Datos

### Estructura de Paciente en `patients.json`
```json
{
  "id": "carlos_68",
  "nombre": "Carlos S.",
  "edad": 68,
  "preferred_patient_model": "mental_llama3.1-8b-mix-sft",
  "last_interaction_file": "2025-12-04_14-32-21_Carlos_S.json",
  ...otros campos...
}
```

### Estructura de Interacción en `/dialogos/`
```json
{
  "timestamp": "2025-12-04T14:32:21.123Z",
  "config": {
    "chatbot_model": "deepseek/deepseek-r1-0528-qwen3-8b",
    "patient_model": "mental_llama3.1-8b-mix-sft",
    "patient_name": "Carlos S.",
    ...
  },
  "messages": [
    {"role": "user", "content": "Hola doctor..."},
    {"role": "assistant", "content": "Hola Carlos..."},
    ...
  ]
}
```

---

## Mejoras Futuras Sugeridas

1. **Límite de Historial**: Implementar truncamiento inteligente del contexto.
2. **Selector de Sesión**: Poder elegir qué interacción previa cargar (no solo la última).
3. **Resumen de Progreso**: Dashboard que muestre la evolución del paciente a lo largo de múltiples sesiones.
4. **Búsqueda en Historial**: Poder buscar interacciones por fecha, tema o palabra clave.
5. **Exportar Historial**: Generar un reporte PDF con todas las interacciones de un paciente.
