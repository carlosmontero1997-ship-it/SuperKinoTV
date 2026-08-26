# Phase 1: Data Ingestion & Controls — Context

**Gathered:** 2026-08-26
**Status:** Ready for planning

<domain>
## Phase Boundary

User can upload/paste historical Keno 20/80 data and configure all analysis parameters (window, pool size, ticket count, band distribution) via sidebar controls. This phase delivers the data input layer and control panel — no analysis or ticket generation logic (those are Phases 2-3).

</domain>

<decisions>
## Implementation Decisions

### Validation Strictness
- **D-01:** Parser is strict — any line not matching `DD/MM/AAAA,N1,...,N20` (20 integers, 1-80, unique) is rejected
- **D-02:** If ANY line fails validation, NO data is loaded — the user must fix all errors before proceeding
- **D-03:** Error reporting must include line number AND specific reason (e.g., "Línea 5: número 95 fuera de rango 1-80")
- **D-04:** Errors are displayed in an expandible list below the input area, not silently skipped

### Error Feedback UX
- **D-05:** Errors shown in a numbered expandible list: "Línea N: motivo del error"
- **D-06:** Clear visual separation between the input area and the error list
- **D-07:** Error list shows total count at a glance: "X líneas con errores"

### Band Distribution Behavior
- **D-08:** When pool size changes, band distribution recalculates proportionally (auto-recalc)
- **D-09:** In Personalizada mode, if Baja+Media+Alta ≠ pool_size, generation is BLOCKED with a message: "La suma (N) no coincide con el pool (M)"
- **D-10:** NO default preset — user must always define distribution (forced Personalizada)
- **D-11:** Band distribution displayed as colored metrics: Baja=azul, Media=amarillo, Alta=rojo

### Data Persistence
- **D-12:** Uploaded/pasted data persists across all Streamlit tabs via session state
- **D-13:** If user uploads a new file while data exists, prompt "¿Reemplazar datos actuales?" before loading
- **D-14:** If both file upload AND text area have content, detect dual sources and ask: "Se detectaron dos fuentes de datos. ¿Cuál desea usar?" Options: "Solo archivo", "Solo texto", "Combinar ambos"
- **D-15:** When combining, merge lines from both sources, deduplicate by date, sort chronologically

### OpenCode's Discretion
- Exact sidebar layout and spacing
- Loading spinner behavior during parse
- Tooltip text on controls
- Color palette for band metrics (specific shades of blue/yellow/red)

</decisions>

<specifics>
## Specific Ideas

- The user is Dominican and works with Keno 20/80 lottery data — all UI text in Spanish
- Strict validation is preferred over lenient — the user wants data integrity above convenience
- "No quiero que se pierda nada silenciosamente" — the user explicitly said errors must be reported, not ignored
- Band distribution is important to the user's analysis workflow — they want full control over the Low/Mid/High split
- The user interacts with the app across multiple tabs — data should be available everywhere without re-uploading

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — DATA-01 through DATA-05, CTRL-01 through CTRL-04
- `.planning/PROJECT.md` — Project context, constraints, key decisions

### Architecture & Conventions
- `.planning/codebase/ARCHITECTURE.md` — Layering strategy (core vs UI)
- `.planning/codebase/CONVENTIONS.md` — Code style, naming, error handling patterns
- `.planning/codebase/STRUCTURE.md` — Package hierarchy, module organization

### Existing Implementation
- `app.py` — Current app.py with all Phase 1 logic already implemented (parse_line, ingest_lines, render_sidebar, render_tab_*)
- `superkino/core/ingest.py` — v1.0 ingestion module (reference for validation patterns)
- `superkino/core/models.py` — Draw/DrawHistory dataclasses (reference for domain model)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `parse_line()` in app.py:78 — Already implements strict DD/MM/AAAA parsing with split-based approach
- `ingest_lines()` in app.py:96 — Multi-line ingestion with duplicate date detection
- `Draw` dataclass in app.py:60 — Frozen dataclass with 20-number validation
- `render_sidebar()` in app.py:168 — Sidebar control rendering (window, pool, tickets, band dist)
- `BAND_LOW/MID/HIGH` constants in app.py:35-37 — Band range definitions
- `BAND_PRESETS` dict in app.py:39 — Preset distribution tuples

### Established Patterns
- Streamlit `st.session_state` for data persistence across tabs
- `st.file_uploader` + `st.text_area` dual-input pattern
- `st.sidebar` for all controls (window, pool size, ticket count, band distribution)
- `st.expander` for error lists
- `st.metric` with delta for band count display

### Integration Points
- Data flows from `ingest_lines()` → `st.session_state.draws` → consumed by all tabs
- Sidebar config dict consumed by all tab render functions
- Band distribution tuple (low, mid, high) feeds into pool generation (Phase 2)

</code_context>

<deferred>
## Deferred Ideas

- Walk-forward backtesting simulator — v2 requirement ENH-03
- Heatmap visualization of presence matrix — v2 requirement ENH-01
- Lift/co-occurrence pair analysis tab — v2 requirement ENH-02
- Temperature-controlled combination generation — v2 requirement ENH-04
- Multi-user support or authentication — out of scope permanently
- Database persistence — out of scope (in-memory session state)

</deferred>

---

*Phase: 01-keno-v1.1*
*Context gathered: 2026-08-26*
