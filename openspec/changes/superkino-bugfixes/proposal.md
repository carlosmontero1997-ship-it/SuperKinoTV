# Proposal: SuperKino Bugfixes

## Why

Las 4 páginas Streamlit del proyecto SuperKino presentan bugs críticos que impiden un uso correcto: un typo en la variable de sesión rompe la app después de cargar datos, la lógica de activación es confusa y falta un import necesario. Estos bugs deben corregirse para que el proyecto sea usable.

## What Changes

- **Corregir typo** en `superkino/app/pages/0_Historial.py` línea 58: cambiar `st.session_history` por `st.session_state.history`
- **Rediseñar lógica** de activación en la misma página: el procesamiento debe ocurrir al hacer clic en el botón, no automáticamente al subir archivo
- **Agregar imports** que faltan al inicio del archivo: `import pytest` y `from typing import List`
- **Reemplazar método "hackeado"** de exportación en `superkino/app/pages/0_Historial.py` por método propiamente definido en `superkino/core/models.py`
- **Eliminar código muerto** del final de `superkino/app/pages/0_Historial.py` (líneas 121-137)

## Capabilities

### Modified Capabilities

- `app/pages/0_Historial.py`: Cuatro arreglos de bugs menores que corrigen comportamiento de la UI sin cambiar requisitos de especificación
- `core/models.py`: Agregar método `to_file_path` a clase `DrawHistory`

### No hay requisito de specs nuevos (cambios puramente de corrección de bugs)

Establecer `skip_specs: true` en `.openspec.yaml` al finalizar.

## Impact

- **Usabilidad**: La app ya no se "rompe" después de cargar un historial
- **Experiencia de usuario**: El botón "Procesar datos" funciona como se espera
- **Mantenibilidad**: El método de exportación queda definido propiamente en el modelo
- **Compatibilidad**: No hay cambios en la API ni en el formato de datos