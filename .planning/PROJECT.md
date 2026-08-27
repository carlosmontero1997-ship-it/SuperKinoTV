# SuperKinoTV — Keno 20/80 Analysis & Ticket Generator

## What This Is

Streamlit-based WebApp for deterministic analysis and ticket generation for the Keno 20/80 (SuperKino TV) lottery game. Users upload historical draw data, the system computes frequency matrices, generates a dynamic pool of top-ranked numbers, and produces wheeling-reduced ticket sets — all 100% deterministic via Python backend algorithms (no LLM hallucinations).

## Core Value

Deterministic combinatorial analysis and wheeling-based ticket generation from historical Keno 20/80 data, with zero random/LLM-generated numbers.

## Current State

**Shipped:** v1.1 (2026-08-26)
**Codebase:** Single `app.py` (1,401 lines), Streamlit 1.62.0, pandas 3.0.5, numpy 2.5.2
**Data:** 120 historical draws (21/04/2026 – 19/08/2026) in SuperKinoTV.txt
**Server:** Running locally at http://localhost:8501

### What v1.1 Delivered

- Strict all-or-nothing data ingestion with dual source detection, session state persistence
- Full 80-number frequency ranking with gap analysis and band color coding
- Deterministic wheeling reduction algorithm with strict blindaje enforcement
- Winning number verification with per-ticket aciertos tracking
- Physical volantes (3 plays each, RD$75 cost) with download capability

## Requirements

### Validated (v1.0)

- ✓ Data ingestion with DD/MM/YYYY,N1,...,N20 format parsing — v1.0
- ✓ Draw validation (range 1-80, 20 unique numbers per draw) — v1.0
- ✓ Presence matrix and frequency computation — v1.0
- ✓ Positional statistics (empirical vs theoretical) — v1.0
- ✓ Pair co-occurrence lift computation — v1.0
- ✓ Temperature-controlled combination generation — v1.0
- ✓ Walk-forward backtesting simulator — v1.0

### Validated (v1.1)

- ✓ Strict all-or-nothing data ingestion with dual source detection — v1.1
- ✓ Forced Personalizada band distribution with auto-recalc — v1.1
- ✓ Full 80-number frequency ranking with band colors — v1.1
- ✓ Gap analysis with cold/hot number identification — v1.1
- ✓ Deterministic wheeling reduction with strict blindaje — v1.1
- ✓ Winning number verification with aciertos tracking — v1.1
- ✓ Physical volantes (3 plays each, RD$75 cost) with download — v1.1

### Active

- [ ] Walk-forward backtesting simulator (BT-01 through BT-05) — v1.2

### Out of Scope

- Real-time draw tracking — offline analysis only
- ML/AI-based number prediction — deterministic algorithms only
- Mobile native app — web-only via Streamlit
- Multi-user authentication — single-user desktop tool
- Database persistence — in-memory session state
- API endpoints — Streamlit UI only

## Context

- **Existing codebase**: v1.1 shipped with single `app.py` (1,401 lines), 3-tab Streamlit layout
- **Data**: 120 historical draws (21/04/2026 – 19/08/2026) in SuperKinoTV.txt
- **Target audience**: Lottery enthusiasts interested in statistical analysis of Keno 20/80
- **Game rules**: Keno 20/80 draws 20 numbers from 1-80; players select up to 10 numbers per ticket
- **Cost structure**: RD$75 per volante (physical ticket with 3 plays/jugadas)

## Constraints

- **Tech stack**: Python 3.11+, Streamlit 1.62.0, pandas 3.0.5, numpy 2.5.2, plotly
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
| Forced Personalizada band dist | User always defines distribution, no presets | ✓ |
| Strict all-or-nothing validation | Any error blocks all data, no partial state | ✓ |
| Greedy pair-coverage wheeling | Deterministic, fast, sufficient for small pool sizes | ✓ |

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
*Last updated: 2026-08-27 after v1.1 milestone completion*
