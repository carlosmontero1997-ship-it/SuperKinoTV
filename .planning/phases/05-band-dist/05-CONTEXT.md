# Phase 5: Dynamic Band Distribution per Ticket — Context

**Date:** 2026-08-27

## Domain
User can select band distribution scheme (4-3-3, 3-4-3, 1-4-4-1, etc.) and wheeling algorithm respects it per ticket. Each 10-number ticket must follow the selected B-M-A distribution.

## Decisions

### Presets de Distribución
- **5 presets offered:** 4-3-3, 3-4-3, 3-3-4, 1-4-4-1, 2-4-4
- **Plus custom option:** User defines B-M-A manually (3 number inputs)
- **UI:** Sidebar selectbox with presets + "Custom" option that reveals 3 number inputs

### Pool vs Boleto Interaction
- **Independientes:** Pool keeps its current band distribution (sidebar Baja/Media/Alta controls pool composition)
- Per-ticket band distribution is an ADDITIONAL filter that selects from the pool
- Pool band controls and ticket band controls are separate concerns

### Validación del Pool
- **Error claro** when pool cannot satisfy the selected distribution
- Example: "Pool no tiene suficientes números Baja (2) para esquema 4-3-3 (necesita 4)"
- No ticket generation until pool has sufficient numbers in each band
- Validate BEFORE wheeling starts, not during

### Uniformidad por Boleto
- **Option to choose:** Uniform (all tickets same distribution) OR Variable (wheeling can vary distribution per ticket)
- UI: Toggle/radio in sidebar: "Distribución uniforme" vs "Variar por boleto"
- Uniform: all tickets follow exact same B-M-A scheme
- Variable: wheeling algorithm can vary distribution across tickets for better coverage

### Algoritmo de Wheeling
- Current `wheeling_reduction()` generates combinations from pool without band constraints
- Must be modified to filter candidates by band distribution before greedy coverage selection
- Candidates must satisfy: count of numbers in each band matches the selected distribution
- If variable mode: allow different distributions per ticket during greedy selection

## Canonical References
- `app.py:325-404` — `wheeling_reduction()` function (needs modification)
- `app.py:270-320` — `generate_dynamic_pool()` with `band_dist` parameter
- `app.py:524-574` — Sidebar band controls (Baja/Media/Alta number inputs)
- `app.py:584-587` — Config dict with `band_dist` key

## Code Context
- **Reusable:** Pool generation with band filtering already exists
- **Integration point:** `wheeling_reduction()` needs new parameter for per-ticket band distribution
- **Pattern:** Sidebar controls follow existing `st.number_input` pattern with session state keys

## Deferred Ideas
- (none)
