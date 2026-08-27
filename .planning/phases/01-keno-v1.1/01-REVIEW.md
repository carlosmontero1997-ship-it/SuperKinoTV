---
phase: 01-keno-v1.1
reviewed: 2026-08-27T00:15:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - app.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-08-27T00:15:00Z
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Phase 1 implementation of `app.py` (944 lines) was reviewed for bugs, security issues, and code quality. The file implements data ingestion, sidebar controls, analysis algorithms, and ticket generation for a Keno 20/80 Streamlit app.

One critical bug was found: the `on_change` callback on the pool size slider passes the local variable `pool_size` as `args`, but this variable is undefined on first render (causing `NameError`) and stale on subsequent renders. The Streamlit session-state best practices explicitly state callbacks should read widget values via `st.session_state.key`, not via captured local variables.

Three warnings were identified: a cost display calculation error using integer division, dead code in the wheeling algorithm from an overwritten assignment, and an unreachable default-values branch in the band recalculation callback.

No security vulnerabilities were found. The app has no external secrets, no database access, no user authentication, and no file system writes beyond Streamlit's download button.

## Critical Issues

### CR-01: `NameError` / stale callback — `args=(pool_size,)` on pool size slider

**File:** `app.py:432-434`
**Issue:** The `st.sidebar.slider` for pool size passes `args=(pool_size,)` to the `_recalc_bands_on_pool_change` callback. The variable `pool_size` is the return value of the same `st.slider()` call — it is being assigned when the function returns. Python evaluates `args=(pool_size,)` before the function returns, so:

- **First render (no existing data):** `render_sidebar()` is never called (line 915-916 returns early), so `pool_size` has never been assigned → `NameError: name 'pool_size' is not defined`.
- **Subsequent renders:** `pool_size` holds the value from the *previous* render, so the callback receives a stale value. The callback's `new_pool` parameter gets the old pool size, not the one the user just selected. The proportional recalculation uses the wrong base, producing incorrect band distributions.

The Streamlit session-state reference (line 83) explicitly states: *"Access a widget's value in its own callback via `st.session_state.key`, not the return variable."*

**Fix:**
```python
# Remove args entirely, read from session_state inside the callback:
pool_size = st.sidebar.slider(
    "Tamano del Pool Dinamico",
    min_value=15,
    max_value=30,
    value=20,
    help="Cantidad de numeros en el pool generado automaticamente.",
    on_change=_recalc_bands_on_pool_change,
    # No args — callback reads st.session_state directly
)

# Update the callback signature:
def _recalc_bands_on_pool_change() -> None:
    """D-08: Recalculate band values proportionally when pool_size changes."""
    new_pool = st.session_state.get("tamano_del_pool_dinamico", 20)
    prev_pool = st.session_state.get("_prev_pool_size", new_pool)
    if new_pool == prev_pool:
        return
    st.session_state["_prev_pool_size"] = new_pool
    # ... rest unchanged, using new_pool from session_state
```

## Warnings

### WR-01: Integer division truncates per-play cost to zero

**File:** `app.py:707`
**Issue:** The per-play cost is calculated as `len(volante) * (COST_PER_VOLANTE // 3)` using integer division. `COST_PER_VOLANTE` is 75 (line 39), so `75 // 3 = 25`. This happens to work for the default volante size of 3 plays, but for any other size the cost is wrong. Additionally, the displayed cost in the expander header (line 709) always shows `RD${COST_PER_VOLANTE}` (75) regardless of how many plays are in the volante. The `vol_cost` variable is computed but never used.

**Fix:**
```python
# Option A: If each volante always costs RD$75 (3 plays at RD$25 each),
# simplify to just show the fixed cost. Remove the unused vol_cost variable:
for vol_idx, volante in enumerate(volantes):
    with st.expander(
        f"Volante #{vol_idx + 1} — {len(volante)} jugada(s) — RD${COST_PER_VOLANTE}"
    ):
        ...

# Option B: If volantes can have variable play counts, calculate correctly:
vol_cost = len(volante) * (COST_PER_VOLANTE / 3)
with st.expander(
    f"Volante #{vol_idx + 1} — {len(volante)} jugada(s) — RD${vol_cost:,.0f}"
):
```

### WR-02: Dead code — overwritten tuple assignment in `wheeling_reduction`

**File:** `app.py:325-327`
**Issue:** Line 325 creates `new_ticket` by copying all elements from `base`, then line 327 immediately overwrites it with a different expression (`list(base[:-1]) + [alt]`). Line 325 is dead code that does nothing.

```python
# Line 325: dead code — result is immediately overwritten
new_ticket = tuple(sorted((alt,) + tuple(x for x in base if True)))
# Line 327: actual assignment
new_ticket = tuple(sorted(list(base[:-1]) + [alt]))
```

**Fix:**
```python
# Remove the dead line 325 entirely:
for alt in pool_sorted:
    if alt not in base:
        new_ticket = tuple(sorted(list(base[:-1]) + [alt]))
        if new_ticket not in candidates and len(new_ticket) == ticket_size:
            candidates.append(new_ticket)
            break
```

### WR-03: Unreachable `else` branch in `_recalc_bands_on_pool_change`

**File:** `app.py:543-547`
**Issue:** The `else` branch (line 543) handles the case where `old_total == 0` by setting proportional defaults. However, this branch is unreachable because `st.number_input` widgets always populate `st.session_state` before any callback fires. By the time `_recalc_bands_on_pool_change` executes, `st.session_state["_band_baja"]`, `st.session_state["_band_media"]`, and `st.session_state["_band_alta"]` always exist (set by the `st.number_input` widgets on lines 461-483). The `.get()` calls on lines 528-530 always return the widget values, never the default `0`. Dead code increases maintenance surface without providing safety.

**Fix:**
```python
def _recalc_bands_on_pool_change() -> None:
    """D-08: Recalculate band values proportionally when pool_size changes."""
    new_pool = st.session_state.get("tamano_del_pool_dinamico", 20)
    prev_pool = st.session_state.get("_prev_pool_size", new_pool)
    if new_pool == prev_pool:
        return
    st.session_state["_prev_pool_size"] = new_pool

    old_baja = st.session_state.get("_band_baja", 0)
    old_media = st.session_state.get("_band_media", 0)
    old_alta = st.session_state.get("_band_alta", 0)
    old_total = old_baja + old_media + old_alta

    if old_total > 0:
        new_baja = max(0, round(new_pool * old_baja / old_total))
        new_media = max(0, round(new_pool * old_media / old_total))
        new_alta = new_pool - new_baja - new_media
        if new_alta < 0:
            new_alta = 0
            new_media = new_pool - new_baja
        st.session_state["_band_baja"] = new_baja
        st.session_state["_band_media"] = new_media
        st.session_state["_band_alta"] = new_alta
    # else branch removed — unreachable since number_input widgets always
    # populate session_state before this callback fires
```

## Info

### IN-01: Unused variable `vol_cost` in `render_tab_tickets`

**File:** `app.py:707`
**Issue:** `vol_cost` is computed (`len(volante) * (COST_PER_VOLANTE // 3)`) but never referenced. The expander header on line 709 uses `COST_PER_VOLANTE` directly.

**Fix:** Remove the `vol_cost` assignment on line 707, or use it in the expander header if the cost should vary by play count (see WR-01).

### IN-02: Duplicate computation of `pool` and `band_counts` across tabs

**File:** `app.py:613` and `app.py:675`
**Issue:** `generate_dynamic_pool(draws, window, pool_size, band_dist)` is called identically in both `render_tab_pool` (line 613) and `render_tab_tickets` (line 675). Since all tabs render on every Streamlit rerun, this computes the same pool twice per interaction. This is a performance concern (out of v1 scope) but also a maintainability concern — if the pool generation logic changes, both call sites must be updated in sync.

**Fix:** Compute the pool once in `main()` and pass it to both tab functions via the config dict:
```python
# In main(), after config is validated:
pool, band_counts = generate_dynamic_pool(draws, config["window"], config["pool_size"], config["band_dist"])
config["pool"] = pool
config["band_counts"] = band_counts
```

---

_Reviewed: 2026-08-27T00:15:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
