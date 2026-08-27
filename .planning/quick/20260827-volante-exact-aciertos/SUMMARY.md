---
slug: volante-exact-aciertos
type: quick
status: complete
created: 2026-08-27
updated: 2026-08-27
---

# Summary: Distribucion de Aciertos Exacta por Volante

## Result

La "Distribucion de Aciertos" en la pestaña de Volantes ahora muestra el **conteo exacto** por cada numero de aciertos (10, 9, 8, 7, 6, 5) en lugar de conteos acumulados "5+", "6+", etc.

- Cada boleta se cuenta en UNA sola columna (la de su numero exacto de aciertos).
- Iteramos en orden descendente (10 → 5) para mejor legibilidad.

## Files Changed

- `app.py` — `verify_numbers_for_volantes` (linea ~500): distribution ahora usa `aciertos_counts.count(n)` por n exacto en vez de `>= threshold`.
- `app.py` — `render_tab_tickets` (linea ~2150): numero de columnas dinamico y sin texto "aciertos" duplicado.

## Verification

- `python -c "import app"` pasa correctamente.
- Sintaxis valida (ast.parse).
