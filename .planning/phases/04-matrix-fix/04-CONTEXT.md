# Phase 4: Matrix Ordering Fix — Context

**Completed:** 2026-08-27 (already implemented in v1.1)

## Domain
Ensure intermediate matrix displays S1 as most recent draw and always uses the 100 most recent draws available.

## Status
**ALREADY IMPLEMENTED** — no new work needed.

## Evidence
- `app.py:144-156`: `compute_intermediate_matrix()` reverses subset → S1 = most recent
- `app.py:149`: `subset = draws[-window:]` takes most recent N draws
- `app.py:489-494`: Window slider defaults to `max_window = min(100, n_draws)`

## Decisions
- S1 = most recent draw (top row) — already implemented
- Window defaults to 100 most recent draws — already implemented
- No changes required

## Canonical References
- `app.py:144-156` — `compute_intermediate_matrix()` function
- `app.py:489-494` — Window slider configuration
