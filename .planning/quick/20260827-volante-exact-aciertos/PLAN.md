---
slug: volante-exact-aciertos
type: quick
status: complete
created: 2026-08-27
updated: 2026-08-27
---

# Quick Task: Distribucion de Aciertos Exacta por Volante

## Description

En la pestaña de Volantes, la "Distribucion de Aciertos" mostraba conteos acumulados usando tabs "5+", "6+", ... (cada uno incluye todos los aciertos >= el umbral). Requisito: mostrar el **conteo exacto** por cada numero de aciertos (5, 6, 7, 8, 9, 10) separados, sin acumular.

## Task

Cambiar la distribucion de aciertos de acumulada a conteo exacto.

## Changes

1. **app.py:500-502** (`verify` / summary `distribution`) — Reemplazar el loop acumulado:
   ```python
   for threshold in [5, 6, 7, 8, 9, 10]:
       distribution[f"{threshold}+"] = len([a for a in aciertos_counts if a >= threshold])
   ```
   por conteo exacto:
   ```python
   for n in range(10, 4, -1):
       distribution[f"{n} aciertos"] = aciertos_counts.count(n)
   ```

2. **app.py:2150-2154** (UI "Distribucion de Aciertos") — `tier` ahora ya incluye "aciertos" en la clave; eliminar la duplicacion y usar numero de columnas dinamico:
   ```python
   dist_cols = st.columns(len(summary["distribution"]))
   for i, (tier, count) in enumerate(summary["distribution"].items()):
       with dist_cols[i]:
           st.metric(tier, count)
   ```

## Files Changed

- `app.py` — `verify_numbers_for_volantes` (distribution) y `render_tab_tickets` (UI)

## Verification

- `python -c "import app"` passes
- Distribution keys now "10 aciertos".."5 aciertos" with exact counts (e.g. 5 tickets with exactly 6 aciertos)
- UI shows a metric column per exact aciertos count

## Summary

status: complete
