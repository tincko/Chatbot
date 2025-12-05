# Simulación del Paso del Tiempo en Conversaciones

## Descripción General

Esta funcionalidad permite que las conversaciones con pacientes simulen el paso del tiempo de manera realista, añadiendo:
1. **Detección Automática**: Al recargar una conversación antigua, el sistema detecta el tiempo transcurrido.
2. **Botón Manual "Nuevo Día"**: Permite forzar un salto temporal durante una sesión activa.

---

## ¿Por Qué es Importante?

En la vida real, las conversaciones terapéuticas no son continuas. Un paciente viene hoy, luego regresa mañana o en unos días. Durante ese tiempo:
- Puede haber tomado o no la medicación
- Pueden surgir nuevos problemas
- Puede haber seguido (o no) los consejos del psicólogo

Esta funcionalidad hace que la simulación sea más realista y útil para entrenamiento.

---

## Método 1: Detección Automática (6+ horas)

### Cómo Funciona

Cuando seleccionas un paciente que tiene historial previo:
1. Se carga el archivo de su última interacción
2. Se compara el `timestamp` de esa interacción con la hora actual
3. Si pasaron **más de 6 horas**, se inyecta automáticamente un mensaje del sistema

### Mensaje del Sistema Inyectado

```
Han pasado X día(s) desde la última conversación (fecha anterior).

Al comenzar esta nueva sesión, el paciente debe:
1. Saludar de nuevo al psicólogo (ej: "Hola doctor", "Buenos días")
2. Contar brevemente qué pasó con la medicación en este tiempo:
   - Si siguió el consejo anterior
   - Si se olvidó de tomar alguna dosis
   - Si hubo algún problema nuevo o cambio en su situación
3. Mantener coherencia con su perfil y conversaciones previas
```

### Efecto en el Comportamiento

El modelo del **paciente** (no el psicólogo) recibe estas instrucciones y:
- Saluda como si fuera un nuevo día
- Reporta eventos que ocurrieron "desde ayer"
- Mantiene coherencia con su perfil y problemas conocidos

**Ejemplo de conversación:**

**Sin salto de tiempo:**
- Usuario: "¿Y hoy cómo te fue?"
- Paciente: "Bien, gracias por preguntar..."

**Con salto de tiempo automático (pasó 1 día real):**
- Usuario: [inicia sesión]
- Paciente (automático): "Hola doctor, buen día. Ayer intenté lo de la alarma que me sugirió, pero me olvidé igual porque salí apurado al trabajo..."

---

## Método 2: Botón Manual "Nuevo Día"

### Ubicación

En la interfaz de chat, en el header, aparece un botón:
- **Ícono**: 🕐 (reloj)
- **Texto**: "Nuevo Día"
- **Posición**: Entre el nombre del paciente y el botón de cerrar (X)

### Cuándo Aparece

El botón solo es visible cuando:
- ✅ No estás en Modo Solitario (`soloMode === false`)
- ✅ Hay un paciente seleccionado (`config.patient_name` existe)
- ✅ Hay mensajes en el chat (`messages.length > 0`)

### Cómo Usarlo

1. Durante una conversación activa con un paciente
2. Haz clic en **"Nuevo Día"**
3. El sistema inyecta un mensaje del sistema (invisible para ti)
4. Continúa la conversación normalmente
5. El paciente responderá como si hubiera pasado un día

### Mensaje del Sistema Inyectado

```
Ha pasado un día completo desde la última conversación.

Al continuar, el paciente debe:
1. Saludar de nuevo al psicólogo
2. Contar qué pasó con la medicación desde ayer
3. Mencionar eventos nuevos relevantes (visita médica, síntomas, trabajo, familia)
4. Mantener coherencia con su perfil y conversaciones previas
```

### Ejemplo de Uso en una Sesión

**Conversación Normal:**
```
Psicólogo: "Intenta poner una alarma para recordar la medicación"
Paciente: "Sí, doctor, voy a probar eso"
```

**[Usuario hace clic en "Nuevo Día"]**

**Sistema inyecta instrucciones (invisible)**

**Conversación Continúa:**
```
Usuario: "Hola"
Paciente: "Hola doctor, buenos días. Mire, ayer probé lo de la alarma... pero igual se me pasó porque estuve muy ocupado en el trabajo. Me olvidé de tomarla a la hora del almuerzo."
```

---

## Diferencias Entre Ambos Métodos

| Característica | Automático (6+ horas) | Manual ("Nuevo Día") |
|----------------|----------------------|----------------------|
| **Trigger** | Al seleccionar paciente con historial antiguo | Click en botón durante sesión activa |
| **Cuándo se usa** | Sesiones separadas en el tiempo real | Durante una misma sesión de práctica |
| **Tiempo simulado** | Basado en tiempo real transcurrido | Siempre 1 día |
| **Control del usuario** | Ninguno (automático) | Total (manual) |
| **Ideal para** | Práctica longitudinal realista | Demostraciones y pruebas rápidas |

---

## Implementación Técnica

### Frontend (`App.jsx`)

#### `selectPatient()` - Detección Automática
```javascript
// Calcular tiempo transcurrido
const lastTimestamp = new Date(data.timestamp);
const now = new Date();
const hoursElapsed = (now - lastTimestamp) / (1000 * 60 * 60);

// Si >6 horas, inyectar mensaje del sistema
if (hoursElapsed > 6) {
    const timeGapMessage = { role: 'system', content: '...' };
    setMessages([timeGapMessage, ...data.messages]);
}
```

#### `simulateNewDay()` - Botón Manual
```javascript
const simulateNewDay = () => {
    const timeGapMessage = { 
        role: 'system', 
        content: 'Ha pasado un día completo...' 
    };
    setMessages(prev => [...prev, timeGapMessage]);
};
```

#### Renderizado de Mensajes
```javascript
// Los mensajes 'system' NO se muestran en la UI
messages.filter(msg => msg.role !== 'system').map((msg, idx) => (
    // Render normal de user/assistant
))
```

---

## Casos de Uso

### Caso 1: Práctica Realista a Largo Plazo
**Escenario**: Estás simulando el seguimiento de un paciente a lo largo de una semana.

1. **Lunes**: Sesión con Carlos S., le sugieres una alarma. Guardas interacción.
2. **Martes** (al día siguiente): Seleccionas a Carlos S.
   - **Automático**: Sistema detecta que pasaron ~24 horas
   - **Resultado**: Carlos saluda y cuenta qué pasó con la alarma
3. **Miércoles**: Repite el proceso
   - Cada día Carlos reporta nuevos eventos: olvidos, síntomas, mejoras

### Caso 2: Demostración Rápida a Estudiantes
**Escenario**: Quieres mostrar cómo evoluciona un caso durante 3 días en 10 minutos.

1. Inicias sesión con Ana López
2. Conversas sobre adherencia
3. Click en **"Nuevo Día"** → Ana saluda de nuevo y reporta progreso
4. Conversas sobre nuevos síntomas
5. Click en **"Nuevo Día"** → Ana reporta evolución
6. Todo en una sola sesión continua

### Caso 3: Pruebas de Coherencia del Modelo
**Escenario**: Verificar que el paciente mantiene memoria de eventos pasados.

1. Sesión 1: María menciona que tiene problemas con su esposo
2. Click en **"Nuevo Día"**
3. Sesión "2": Esperas que María mencione coherentemente algo sobre su esposo
   - ✅ Correcto: "Ayer hablé con mi esposo y quedamos en..."
   - ❌ Incorrecto: No menciona nada, como si no hubiera pasado

---

## Ventajas de Esta Implementación

1. **Realismo**: Las simulaciones se sienten más como casos clínicos reales.
2. **Flexibilidad**: Puedes trabajar a tu ritmo (automático) o acelerar (manual).
3. **Transparencia**: Los mensajes del sistema no se muestran al usuario, evitando confusión.
4. **Coherencia**: El modelo paciente mantiene memoria de eventos previos.
5. **Entrenamiento**: Útil para practicar seguimiento y evolución de casos.

---

## Limitaciones y Consideraciones

### 1. Dependencia de la Calidad del Modelo
- Modelos menos sofisticados pueden ignorar las instrucciones del sistema.
- Algunos modelos pueden mencionar explícitamente "pasó un día" (lo cual se les instruye NO hacer).

### 2. Longitud del Contexto
- Cada mensaje del sistema consume tokens del contexto.
- Si se usa "Nuevo Día" muchas veces en una sesión, puede llenar el contexto.
- **Solución**: Resetear la conversación ocasionalmente.

### 3. Coherencia de Eventos Generados
- Los modelos "inventan" lo que pasó durante el día (ej: "olvidé la pastilla").
- Estos eventos son aleatorios pero guiados por el perfil del paciente.
- Pueden variar en realismo según el modelo.

### 4. No Afecta al Psicólogo
- El modelo del psicólogo NO recibe las instrucciones de salto temporal.
- Depende de la conversación del paciente para darse cuenta del paso del tiempo.

---

## Mejoras Futuras

### 1. Selector de Tiempo
En lugar de solo "1 día", permitir:
- "2-3 días"
- "1 semana"
- "1 mes"

### 2. Eventos Programados
Permitir definir eventos específicos que "ocurrieron":
- "Durante este día, el paciente tuvo una cita con cardiología"
- "Durante este día, el paciente olvidó todas las dosis"

### 3. Resumen de Tiempo Transcurrido
Mostrar visualmente cuánto "tiempo simulado" ha pasado en total:
- "Esta es la sesión #5 con Carlos, ~2 semanas de seguimiento"

### 4. Línea de Tiempo Interactiva
Dashboard que muestre:
- Cuándo fue cada sesión
- Eventos clave mencionados
- Progreso en adherencia a lo largo del tiempo

---

## Configuración

### Umbral de Tiempo Automático

Por defecto: **6 horas**

Para cambiar este valor, edita `App.jsx`:

```javascript
// Línea actual:
if (hoursElapsed > 6) {

// Para 12 horas:
if (hoursElapsed > 12) {

// Para 24 horas (1 día completo):
if (hoursElapsed > 24) {
```

### Personalizar Mensajes del Sistema

Los mensajes están en español y pueden ser modificados en:
- `selectPatient()` → Detección automática
- `simulateNewDay()` → Botón manual

---

## Consejos de Uso

1. **Para Entrenamientos Largos**: Deja que la detección automática funcione naturalmente.
2. **Para Demos**: Usa el botón "Nuevo Día" para acelerar la simulación.
3. **Para Evaluar Modelos**: Prueba qué tan bien mantienen coherencia a través del tiempo.
4. **Para Casos Complejos**: Combina ambos métodos según necesites.

---

## Preguntas Frecuentes

**Q: ¿Los mensajes del sistema se guardan en las interacciones?**
A: Sí, se guardan en el JSON pero no se muestran en la UI del chat.

**Q: ¿Puedo usar "Nuevo Día" varias veces seguidas?**
A: Sí, pero puede confundir al modelo. Usa con moderación.

**Q: ¿Funciona en Modo Solitario?**
A: No, porque no hay paciente que simule el paso del tiempo.

**Q: ¿El psicólogo sabe que pasó tiempo?**
A: Solo indirectamente, a través de lo que dice el paciente.

**Q: ¿Puedo desactivar la detección automática?**
A: Sí, comenta o elimina la lógica en `selectPatient()`.
