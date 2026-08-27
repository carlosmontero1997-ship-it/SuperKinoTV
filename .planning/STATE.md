# State

## Current Status
- Project: SuperKinoTV
- Milestone: v1.2 Backtesting & Band Distribution
- Current Phase: 7 — Predictive Analysis (next)
- Codebase: Single app.py (1,839 lines)
- Git: Initialized

## Recent Changes
- v1.1 shipped and archived (3 phases, 2026-08-26)
- v1.2 milestone started
- Phase 5 completed: Dynamic Band Distribution per Ticket (2026-08-27)
- Phase 6 completed: Walk-Forward Backtesting Engine (2026-08-27)
- Phase 7 planning completed (2026-08-27)

## Pending Items
- Phase 7: Predictive Analysis (BT-06, 1 plan)

## Known Issues
- None

## Decisions
- Phase 5: Renamed "1-4-4-1" preset to "1-4-5" (tickets have 10 numbers across 3 bands, must sum to 10)
- Phase 6: Temperature T uses softmax weighting on frequency scores for pool selection
- Phase 6: Walk-forward validation uses fixed training window, test=1 draw, step=1
- Phase 6: Backtesting tab temperature overrides sidebar T for backtesting runs only

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-27)

**Core value:** Deterministic combinatorial analysis and wheeling-based ticket generation
**Current focus:** v1.2 — executing phases
