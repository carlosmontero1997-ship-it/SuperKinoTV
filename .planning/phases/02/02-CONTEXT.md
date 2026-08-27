# Phase 2: Analysis Matrices & Pool Generation — Context

**Gathered:** 2026-08-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Display intermediate frequency matrices (100×20 and 10×10) and generate a ranked dynamic pool from statistical analysis. This phase builds on the data ingestion layer (Phase 1) and provides the analytical foundation for ticket generation (Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Matrix Display
- **D-01:** 100×20 intermediate matrix displays all draws with 20 sorted positions — each row is one draw, columns are positions 1-20
- **D-02:** 10×10 positional frequency matrix groups numbers by adjacent lane pairs (C1=B1-B2, C2=B3-B4, ..., C10=B19-B20)
- **D-03:** Matrix displayed using `st.dataframe` with appropriate formatting for readability
- **D-04:** Color coding: cells with presence highlighted, empty cells neutral

### Pool Generation
- **D-05:** Dynamic pool generated from deduplicated frequency + co-occurrence ranking
- **D-06:** Pool size controlled by sidebar slider (15-30, default 20) — already implemented in Phase 1
- **D-07:** Band distribution (Baja/Media/Alta) enforced on pool — counts must match sidebar configuration
- **D-08:** Pool numbers sorted ascending, displayed with band color coding (Baja=blue, Media=yellow, Alta=red)

### Statistical Analysis
- **D-09:** Frequency analysis shows appearance count per number across window
- **D-10:** Co-occurrence analysis shows pair frequency (how often two numbers appear together)
- **D-11:** Gap analysis shows number of draws since each number last appeared

### OpenCode's Discretion
- Exact matrix cell formatting (font size, padding)
- Frequency table layout (single table vs split by band)
- Pool display format (numbered list vs grid vs badge)
- Tab layout within Matrices Intermedias

</decisions>

<specifics>
## Specific Ideas

- The user is Dominican and works with Keno 20/80 lottery data — all UI text in Spanish
- Matrix display should be scannable — user wants to quickly identify patterns
- Pool generation should feel "smart" — not just top-N by frequency, but considers co-occurrence
- Band distribution enforcement ensures pool matches user's configured Baja/Media/Alta split
- Window slider (from Phase 1) controls how many historical draws are analyzed

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — MATX-01, MATX-02, POOL-01, POOL-02

### Architecture & Conventions
- `.planning/PROJECT.md` — Project context, constraints
- `app.py` — Current implementation with Phase 1 data ingestion layer

### Existing Implementation
- `app.py:render_tab_matrices()` — Current matrix tab (needs enhancement)
- `app.py:render_tab_pool()` — Current pool tab (needs enhancement)
- `app.py:generate_dynamic_pool()` — Current pool generation algorithm

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generate_dynamic_pool()` in app.py — Already implements frequency-based pool generation
- `render_tab_matrices()` in app.py — Current matrix rendering (100×20 display)
- `render_tab_pool()` in app.py — Current pool display with band metrics
- `Draw` dataclass — Contains date_iso and numbers tuple
- Session state persistence from Phase 1 — draws available across tabs

### Established Patterns
- Streamlit `st.dataframe` for tabular data
- `st.metric` for summary statistics
- `st.expander` for detailed views
- Band color coding (Baja=blue, Media=yellow, Alta=red) from Phase 1

### Integration Points
- Data flows from `st.session_state.draws` (Phase 1) → matrix analysis → pool generation
- Sidebar config (window, pool_size, band_dist) controls analysis parameters
- Pool output feeds into Phase 3 (wheeling & volantes)

</code_context>

<deferred>
## Deferred Ideas

- Walk-forward backtesting simulator — v2 requirement ENH-03
- Heatmap visualization of presence matrix — v2 requirement ENH-01
- Temperature parameter control T ∈ [0.05, 2.0] — v2 requirement
- SQLite persistence for computed results — out of scope (in-memory session state)

</deferred>

---

*Phase: 02-keno-v1.1*
*Context gathered: 2026-08-27*
