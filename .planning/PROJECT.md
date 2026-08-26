# SuperKinoTV v1.1 — Keno 20/80 Analysis & Ticket Generator

## What This Is

Streamlit-based WebApp for deterministic analysis and ticket generation for the Keno 20/80 (SuperKino TV) lottery game. Users upload historical draw data, the system computes frequency matrices, generates a dynamic pool of top-ranked numbers, and produces wheeling-reduced ticket sets — all 100% deterministic via Python backend algorithms (no LLM hallucinations).

## Core Value

Deterministic combinatorial analysis and wheeling-based ticket generation from historical Keno 20/80 data, with zero random/LLM-generated numbers.

## Requirements

### Validated

- ✓ Data ingestion with DD/MM/YYYY,N1,...,N20 format parsing — v1.0
- ✓ Draw validation (range 1-80, 20 unique numbers per draw) — v1.0
- ✓ Presence matrix and frequency computation — v1.0
- ✓ Positional statistics (empirical vs theoretical) — v1.0
- ✓ Pair co-occurrence lift computation — v1.0
- ✓ Temperature-controlled combination generation — v1.0
- ✓ Walk-forward backtesting simulator — v1.0

### Active

- [ ] FR-01: Dual data ingestion (file upload .txt/.csv + text area paste)
- [ ] FR-02: Sort-by-ascending sort on each draw's 20 numbers
- [ ] FR-03: Sliding window selector (max 100 retroactive draws)
- [ ] FR-04: Dynamic Pool size selector (15-30 numbers, default 20)
- [ ] FR-05: Ticket quantity selector (6-30 tickets, default 18)
- [ ] FR-06: Band distribution selector (Low 01-26, Mid 27-54, High 55-80)
- [ ] FR-07: Tab 1 — 100×20 intermediate matrix display
- [ ] FR-08: Tab 1 — 10×10 positional frequency matrix (grouped by adjacent lane pairs)
- [ ] FR-09: Tab 2 — Dynamic Pool with deduplicated frequency+co-occurrence ranking
- [ ] FR-10: Tab 2 — Pool band metrics (Low/Mid/High counts)
- [ ] FR-11: Tab 3 — Deterministic wheeling reduction algorithm
- [ ] FR-12: Tab 3 — Physical volantes (3 tickets each, RD$75 cost per volante)
- [ ] FR-13: Tab 3 — Strict blindaje (0 out-of-pool numbers, ascending sort, 0 duplicates)
- [ ] FR-14: Tab 3 — Download button for generated tickets (.txt)
- [ ] Q-01: App renders correctly in Streamlit with sidebar + tabs layout

### Out of Scope

- Real-time draw tracking — offline analysis only
- ML/AI-based number prediction — deterministic algorithms only
- Mobile native app — web-only via Streamlit
- Multi-user authentication — single-user desktop tool
- Database persistence — in-memory session state
- API endpoints — Streamlit UI only

## Context

- **Existing codebase**: v1.0 MVP shipped with 5-page Streamlit app, core analysis engine, scoring, simulation
- **Data**: 120 historical draws (21/04/2026 – 19/08/2026) in SuperKinoTV.txt
- **Target audience**: Lottery enthusiasts interested in statistical analysis of Keno 20/80
- **Game rules**: Keno 20/80 draws 20 numbers from 1-80; players select up to 10 numbers per ticket
- **Cost structure**: RD$75 per volante (physical ticket with 3 plays/jugadas)

## Constraints

- **Tech stack**: Python 3.11+, Streamlit, pandas, numpy, itertools
- **Determinism**: All combinatorial/extraction logic must be pure Python backend — no LLM number generation
- **Performance**: Must handle up to 100-draw window with 80-number matrix efficiently
- **Wheeling**: Deterministic reduction, not random sampling; 0 duplicates guaranteed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single app.py file | User requested complete, executable code in one block | ✓ |
| Streamlit tabs layout | 3-tab structure: Matrices, Pool, Tickets | ✓ |
| Band tri-split (26/28/26) | Low 01-26, Mid 27-54, High 55-80 matches Keno distribution | ✓ |
| RD$75 per volante | Dominican Republic standard lottery ticket cost | ✓ |
| Wheeling over random sampling | Deterministic reduction guarantees coverage | ✓ |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-26 after initialization*
