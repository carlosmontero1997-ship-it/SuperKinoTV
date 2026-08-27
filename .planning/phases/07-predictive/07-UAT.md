---
status: complete
phase: 07-predictive
source: [07-01-SUMMARY.md]
started: 2026-08-27T15:50:46Z
updated: 2026-08-27T16:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Analisis bajo demanda
expected: El analisis predictivo se ejecuta SOLO al hacer click en 'Ejecutar Analisis Predictivo'. Al cambiar sliders (ventana, temperatura), NO debe recalcularse hasta presionar el boton.
result: issue
reported: "exacto, asi es como deberia pasar segun describes"
severity: major
fixed: yes
fix_plan: 07-02

## Summary

total: 1
passed: 0
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "El analisis predictivo se ejecuta SOLO al hacer click en 'Ejecutar Analisis Predictivo'. Al cambiar sliders NO debe recalcularse hasta presionar el boton."
  status: resolved
  reason: "User reported el analisis se carga siempre, no solo al hacer click"
  severity: major
  test: 1
  artifacts: [app.py:2577, app.py:2311-2331]
  missing: [computed cooc matrix cached in pred_cooc, temp effect cached in bt_temp_results, stale-param captions]
