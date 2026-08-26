# Design: SuperKino Bugfixes

## Context

Proyecto SuperKino con 4 páginas Streamlit que presentan bugs menores pero críticos que afectan la usabilidad. El cambio es puramente de corrección (refactor) sin cambios en el comportamiento de especificación. Las 4 páginas involucradas son `superkino/app/pages/0_Historial.py` y el modelo `superkino/core/models.py`.

## Goals

- Corregir el typo que rompe la app después de cargar datos
- Rediseñar la lógica de activación para que el botón funcione como se espera
- Agregar los imports que faltan para evitar errores de sintaxis
- Reemplazar el método "hackeado" de exportación por uno propiamente definido
- Limpiar el código muerto al final del archivo

## Non-Goals

- No cambiar el formato de datos ni la API de la app
- No agregar nuevas funcionalidades ni capacidades
- No reestructurar el proyecto completo

## Decisions

### D1. Corregir typo en `0_Historial.py` (línea 58)

- **Cambio**: `st.session_history` → `st.session_state.history`
- **Razón**: `session_history` no existe; la variable correcta se llama `session_state.history`. Sin este arreglo, la app lanza `AttributeError` después de procesar los datos.
- **Alternativa considerada**: Mantener `st.session_history` como aliasDepositar: No, el nombre es inconsistente con el patrón `session_state` usado en toda la app.

### D2. Rediseñar lógica de activación en `0_Historial.py` (líneas 40-42)

- **Cambio**: Cambiar de `if st.button(...) or (uploaded_file is not None ...)` a `if st.button(...)` sole
- **Razón**: La lógica original activaba el procesamiento automáticamente al subir un archivo, haciendo el botón redundante. El nuevo comportamiento requiere hacer clic en "Procesar datos" para procesar los datos, lo que es más predecible.
- **Alternativa considerada**: Mantener el procesamiento automático pero añadir un mensaje informativo. Descartado: confunde al usuario al procesar datos sin que él lo espere.

### D3. Agregar imports que faltan en `0_Historial.py`

- **Cambio**: Añadir `import pytest` y `from typing import List` al inicio del archivo
- **Razón**: `List` es usado en la firma de `ingest_lines()` y `pytest` podría ser necesario para testsfuture. Sin estos imports, el módulo falla en tiempo de importación.
- **Alternativa considerada**: Usar tipos genéricos en lugar de `List`, pero esto requeriría cambios mayores en la firma de funciones.

### D4. Reemplazar método "hackeado" en `0_Historial.py` (líneas 121-137)

- **Cambio**: Eliminar el `MethodType` patch y usar el método `to_file_path` definido propiamente en `core/models.py`
- **Razón**: El método `to_file_path_returns_data` creado con `types.MethodType` es frágil, difícil de mantener y no sigue el patrón del proyecto. El método `to_file_path` en `models.py` es la forma correcta.
- **Alternativa considerada**: Mantener el patch pero documentarlo mejor. Descartado: viola el principio de "código claro sobre ingenioso".

### D5. Limpiar código muerto (líneas 121-137 de `0_Historial.py`)

- **Cambio**: Eliminar las últimas 17 líneas que definen y anexan el método `to_file_path_returns_data`
- **Razón**: Una vez que el método propiamente está en `models.py`, el "hack" al final es redundante y añade ruido visual.

## Risks / Trade-offs

- **[R1] Cambiar la lógica de activación puede sorprender a usuarios acostumbrados al procesamiento automático**: Mitigado con documentación clara en la UI y notas en el changelog.
- **[R2] El método `to_file_path` en `models.py` podría no ser llamado si el import falla**: Mitigado asegurando que el import de `core.models` funcione correctamente (already verified).
- **[R3] Users que hayan usado el botón "Exportar" antes del arreglo**: El método antiguo deja de funcionar; se les informará en el changelog y podrán usar el nuevo método.

## Migration Plan

1. Aplicar arreglos a `superkino/app/pages/0_Historial.py`
2. Agregar `to_file_path` a `superkino/core/models.py`
3. Probar flujo completo: upload → procesar → exportar
4. Desplegar actualización a Streamlit Community Cloud

## Open Questions

- Ninguno: todos los arreglos están definidos y sondeables.