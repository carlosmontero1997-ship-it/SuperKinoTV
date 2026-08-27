# State

## Current Status
- Project: SuperKinoTV
- Milestone: v1.2 Backtesting & Band Distribution
- Current Phase: Complete (all 4 phases done)
- Codebase: Single app.py (2,747 lines)
- Git: Initialized

## Recent Changes
- v1.1 shipped and archived (3 phases, 2026-08-26)
- v1.2 milestone started
- Phase 5 completed: Dynamic Band Distribution per Ticket (2026-08-27)
- Phase 6 completed: Walk-Forward Backtesting Engine (2026-08-27)
- Phase 7 completed: Predictive Analysis & Optimization (2026-08-27)
- v1.2 milestone complete

## Pending Items
- None — v1.2 milestone fully complete

## Known Issues
- None

## Decisions
- Phase 5: Renamed "1-4-4-1" preset to "1-4-5" (tickets have 10 numbers across 3 bands, must sum to 10)
- Phase 6: Temperature T uses softmax weighting on frequency scores for pool selection
- Phase 6: Walk-forward validation uses fixed training window, test=1 draw, step=1
- Phase 6: Backtesting tab temperature overrides sidebar T for backtesting runs only
- Phase 7: 6-factor scoring weights: frequency 0.25, gap 0.15, co-occurrence 0.20, recency 0.15, temporal 0.10, band_trend 0.15
- Phase 7: Predictive tab has its own temperature override (sidebar T preserved for pool/ticket generation)
- Phase 7: Standalone co-occurrence matrix extraction (existing compute_frequency_ranking untouched)

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-27)

**Core value:** Deterministic combinatorial analysis and wheeling-based ticket generation
**Current focus:** v1.2 — milestone complete
