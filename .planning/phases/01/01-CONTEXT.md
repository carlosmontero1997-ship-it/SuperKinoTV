# Phase 1: Core Analysis Engine — Context Decisions

## Domain
This phase implements the core statistical analysis engine for SuperKino (Dominican Republic Keno) lottery data analysis. It provides matrix calculations, gap analysis, number scoring, and temperature-controlled generation.

## Core Value
Deterministic statistical analysis of lottery draws without ML-based number generation — all algorithms run in Python without hallucinations.

## Decisions Captured

### Data Ingestion & Format
- **Line format**: `DD/MM/YYYY,N1,N2,...,N20` per draw
- **Ascending sort**: All 20 numbers sorted ascending after parsing
- **Validation**: 
  - Format validation: `DD/MM/YYYY,N1,...,N20` pattern
  - Range validation: Numbers must be 1-80
  - Count validation: Exactly 20 numbers per line
- **Error handling**: Invalid lines are logged and skipped; valid data is integrated

### Matrix Calculations
- **Mobile matrix 100×20**: Processed from historical draw data
- **Positional matrix 10×10**: Frequencies grouped by adjacent cable pairs (C1 = B1-B2, ..., C10 = B19-B20)
- **Gap statistics**: Frequency, last-seen, lift calculations per number per position
- **All calculations deterministic** — no random number generation by LLM

### Number Generation
- **Temperature-controlled softmax**: T ∈ [0.05, 2.0] for probability distribution
- **Pool dynamic ranking**: Based on des-duplicated frequency + co-occurrence ranking
- **Wheeling algorithm**: Deterministic combinatorial reduction on pool
- **Output format**: 3 juegas per volante, costs RD$75 per volante, numbers always sorted ascending within each ticket, 0 duplicate/permuted tickets

### UI Integration
- **Streamlit interface**: 4 tabs (Matrices Intermedias, Pool Dinámico, Volantes & Reducción, Descarga)
- **Sidebar controls**:
  - Ventana móvil slider (max 100 sorteos retroactivos)
  - Tamaño pool dinámico slider (15-30, default 20)
  - Cantidad de boletos slider (6-30, default 18)
  - Distribución por franja (Baja 01-26, Media 27-54, Alta 55-80)

### Key Constraints
- 0 numbers outside the dynamic pool
- Numbers strictly ordered menor a mayor in each ticket
- 0 duplicated or permuted tickets
- Honest statistics: theoretical floors always visible
- Comparison against random baseline mandatory

### Canonical References
- `.planning/codebase/STACK.md` — Stack overview and dependencies
- `.planning/codebase/ARCHITECTURE.md` — Layering strategy
- `.planning/codebase/STRUCTURE.md` — Code structure
- `.planning/codebase/INTEGRATIONS.md` — Integrations and data flows
- `.planning/codebase/CONVENTIONS.md` — Code conventions
- `.planning/codebase/TESTING.md` — Test framework and coverage
- `.planning/codebase/CONCERNS.md` — Known concerns and open questions

### Open Questions / Deferred
- Optimal temperature parameter range for number generation
- Frequency of database re-seeding from source data
- Whether to include user result comparison in core module or UI layer
- Extended number ranges beyond 1-80

## Next Steps
- Proceed to `/gsd-plan-phase 1` to plan implementation tasks
- Research domain patterns and edge cases
- Generate test cases for ingest validation and matrix calculations