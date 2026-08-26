## 1. Arreglar typo en sesión

- [ ] 1.1 Modificar `superkino/app/pages/0_Historial.py` línea 58: cambiar `st.session_history` por `st.session_state.history`
- [ ] 1.2 Verificar: `streamlit run superkino/app/pages/0_Historial.py` carga sin errores y el reporte de calidad aparece correctamente después de procesar un archivo mínimo

## 2. Rediseñar lógica de activación

- [ ] 2.1 Modificar `superkino/app/pages/0_Historial.py` líneas 40-42: cambiar la condición `if st.button(...) or (uploaded_file is not None ...)` por `if st.button(...)` sole
- [ ] 2.2 Verificar: hacer clic en "Procesar datos" procesa los datos, mientras que subir archivo solo los carga sin procesar automáticamente

## 3. Agregar imports que faltan

- [ ] 3.1 Añadir `import pytest` y `from typing import List` al inicio de `superkino/app/pages/0_Historial.py` (después de los otros imports)
- [ ] 3.2 Verificar: `python3 -c "import superkino.app.pages.0_Historial; print('OK')"`

## 4. Reemplazar método "hackeado" de exportación

- [ ] 4.1 Agregar método `to_file_path` a `superkino/core/models.py` (método propiamente definido, no patch via types.MethodType)
- [ ] 4.2 Eliminar líneas 121-137 de `superkino/app/pages/0_Historial.py` (el patch Types.MethodType y su llamada)
- [ ] 4.3 Verificar: `streamlit run superkino/app/pages/0_Historial.py` → botón "Exportar historial a txt" funciona y descarga el archivo correctamente

## 5. Pulir y verificar todo el flujo

- [ ] 5.1 Ejecutar `streamlit run superkino/app/pages/0_Historial.py` y probar el flujo completo: upload .txt → reporte de calidad → tabla de sorteos → exportar .txt
- [ ] 5.2 Verificar que los 120 sorteos originales dan 119 válidos y 1 rechazado (línea con 23 duplicado)
- [ ] 5.3 Verificar que el hueco 04/07/2026 se detecta y muestra como advertencia
- [ ] 5.4 Ejecutar pytest sobre los tests existentes: `pytest superkino/tests/test_core.py -v`