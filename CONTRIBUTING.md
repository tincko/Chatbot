# Guía de Contribución

¡Gracias por tu interés en contribuir a este proyecto! 🎉

## Cómo Contribuir

### Reportar Bugs

Si encuentras un error:

1. **Verifica** que no exista un issue similar
2. **Abre un nuevo issue** con:
   - Descripción clara del problema
   - Pasos para reproducirlo
   - Comportamiento esperado vs actual
   - Screenshots si aplica
   - Información del sistema (OS, versión de Python/Node, etc.)

### Sugerir Mejoras

Para proponer nuevas características:

1. **Abre un issue** describiendo:
   - El problema que resolvería
   - La solución propuesta
   - Alternativas consideradas
   - Impacto en usuarios existentes

### Pull Requests

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/mi-nueva-caracteristica
   ```
3. **Haz tus cambios** siguiendo las guías de estilo
4. **Prueba** tus cambios exhaustivamente
5. **Commit** con mensajes descriptivos:
   ```bash
   git commit -m "feat: agregar análisis de sentimientos"
   ```
6. **Push** a tu fork:
   ```bash
   git push origin feature/mi-nueva-caracteristica
   ```
7. **Abre un Pull Request** con:
   - Descripción clara de los cambios
   - Referencias a issues relacionados
   - Screenshots/videos si aplica

## Guías de Estilo

### Python (Backend)

- Sigue [PEP 8](https://peps.python.org/pep-0008/)
- Usa type hints cuando sea posible
- Documenta funciones complejas con docstrings
- Ejemplo:

```python
def analyze_interaction(
    interaction_data: Dict[str, Any],
    model: str
) -> Dict[str, str]:
    """
    Analiza una interacción terapéutica usando un LLM.
    
    Args:
        interaction_data: Datos de la interacción
        model: Nombre del modelo LLM a usar
        
    Returns:
        Diccionario con el análisis generado
    """
    # Tu código aquí
    pass
```

### JavaScript/React (Frontend)

- Usa componentes funcionales con hooks
- Nombres de componentes en PascalCase
- Nombres de funciones en camelCase
- Agrupa imports lógicamente
- Ejemplo:

```javascript
import React, { useState, useEffect } from 'react';

function MyComponent({ prop1, prop2 }) {
  const [state, setState] = useState(null);
  
  useEffect(() => {
    // Side effects
  }, []);
  
  return (
    <div>
      {/* JSX */}
    </div>
  );
}

export default MyComponent;
```

## Convenciones de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva característica
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formateo, no cambia lógica
- `refactor:` Refactorización de código
- `test:` Agregar/modificar tests
- `chore:` Tareas de mantenimiento

Ejemplos:
```
feat: agregar exportación a CSV
fix: corregir timeout en análisis
docs: actualizar README con nuevas instrucciones
```

## Configuración del Entorno de Desarrollo

### Backend

```bash
cd web_app/backend
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si existe
```

### Frontend

```bash
cd web_app/frontend
npm install
npm run dev
```

## Testing

Antes de hacer un PR:

1. **Backend**: Asegúrate de que el servidor inicie sin errores
2. **Frontend**: Verifica que la UI funcione correctamente
3. **Integración**: Prueba el flujo completo de la aplicación

## Preguntas

Si tienes dudas, no dudes en:
- Abrir un issue con la etiqueta `question`
- Revisar issues existentes
- Consultar la documentación

¡Agradecemos tu colaboración! 🙌
