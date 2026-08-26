# Architecture Decisions

## Layering Strategy
- **Core layer** (`superkino/core/`): Pure Python analysis modules with no Streamlit imports. Testable in isolation via pytest.
- **UI layer** (`superkino/app/`): Streamlit-specific components. Depends on core layer for all analysis logic.

## Data Flow
1. Raw data (`SuperKinoTV.txt`) → `ingest.py` parser/validator
2. Validated draws → `analysis.py` for matrix/gap calculations
3. Analysis results → `scoring.py` for number temperature/scoring
4. Simulator results → `simulator.py` walk-forward backtest vs hypergeometric baseline
5. UI displays results from all layers via Streamlit callbacks

## Persistence Strategy
- SQLite (`data/superkino.db`) for computed results
- Raw text data stored unversioned in project root
- DB re-seeded from `SuperKinoTV.txt` on fresh start

## Validation
- Honest statistics: theoretical floors always visible
- Comparison against random baseline mandatory
- All scores include comparison to random expectation