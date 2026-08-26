# Phase 3: Quality & Polish — Context Decisions

## Domain
This phase implements quality assurance, testing, documentation, and deployment infrastructure for the SuperKino (Dominican Republic Keno) lottery analysis application. All quality gates are deterministic and Python-based, with no model-generated content.

## Core Value
Deterministic quality assurance for lottery analysis application — all tests, documentation, and deployment pipelines are implemented in Python with full traceability and repeatability.

## Decisions Captured

### Test Suite Structure
- **Test framework**: `pytest` configured in `pyproject.toml`
- **Test location**: `tests/test_core.py` covering core modules
- **Test modules without Streamlit dependencies**:
  - `test_models.py` — Draw dataclass validation, DrawHistory operations
  - `test_ingest.py` — Line parser, format validation, gap detection
  - `test_analysis.py` — Matrices, gaps, lift, sums/parity/decades calculations
  - `test_scoring.py` — Individual number scores, temperature generation
  - `test_simulator.py` — Walk-forward backtest, hypergeometric reference comparison

### Test Coverage Priorities
- **Unit tests**: Core functions in `superkino/core/` without Streamlit imports
- **Integration tests**: Core → UI data flow (manual verification)
- **Hypergeometric baseline**: All statistical comparisons include random baseline
- **Theoretical floors**: Always visible in test output
- **Temperature range**: Tests across T ∈ [0.05, 2.0] for number generation

### Quality Gates
- **Honest statistics**: Theoretical floors always visible in test results
- **Random baseline comparison**: Mandatory in all statistical assertions
- **Code conventions**: `black` formatting, NumPy docstrings for core modules
- **Import order**: Standard library → third-party → local application imports
- **Error handling**: Core module errors raise specific exception types

### Documentation Structure
- **PROJECT.md**: Project context, goals, core value, constraints (from Phase 1)
- **REQUIREMENTS.md**: 18 functional requirements, v1/v2 categorization, out of scope
- **ROADMAP.md**: 4-phase roadmap, MVP mode, success criteria per phase
- **STATE.md**: Project memory, recent changes, pending items
- **CONTEXT.md per phase**: Phase 1 (analysis), Phase 2 (UI), Phase 3 (this phase)
- **CODEBASE map**: 7-file `.planning/codebase/` map (STACK through CONCERNS)
- **Onboarding SUMMARY.md**: Light index of learnings and next commands

### Deployment Configuration
- **Entry point**: `streamlit run superkino/app/Home.py`
- **Dependencies**: `streamlit>=1.35.0`, `pandas>=2.2.0`, `numpy>=1.26.0`, `scipy>=1.12.0`, `plotly>=5.18.0`
- **Python**: 3.11+ compatibility
- **Database**: SQLite (`data/superkino.db`), re-seeded from `SuperKinoTV.txt`
- **No build step**: Pure Python application, `pip install -r requirements.txt`

### CI Considerations (planned)
- `pytest tests/` — run test suite
- `pytest --cov=superkino tests/` — with coverage
- No CI configured yet; run locally
- Future: GitHub Actions or similar

### Code Quality Gates
- **Black formatting**: All Python files formatted with black
- **Type hints**: Used where beneficial, not obsessively
- **Docstrings**: NumPy format for core modules
- **Import ordering**: Standard → third-party → local
- **Error types**: Specific exceptions for core modules, user-friendly in UI

### Canonical References
- `.planning/codebase/STACK.md` — Python 3.11+, pytest, black, pandas, numpy, scipy, plotly
- `.planning/codebase/ARCHITECTURE.md` — Core/UI layering, quality gate strategy
- `.planning/codebase/STRUCTURE.md` — Package hierarchy, test locations
- `.planning/codebase/INTEGRATIONS.md` — SQLite integration, deployment setup
- `.planning/codebase/CONVENTIONS.md` — Quality conventions, naming standards
- `.planning/codebase/TESTING.md` — Test framework, coverage criteria, running tests
- `.planning/codebase/CONCERNS.md` — Known quality issues, numerical stability, performance concerns

### Open Questions / Deferred
- **Optimal test coverage percentage**: Target for v1 vs v2
- **Database re-seeding**: Frequency and UX for re-seeding from source data
- **User result comparison**: Core module vs UI layer placement
- **Extended test types**: Property-based testing, fuzz testing
- **CI/CD pipeline**: Choice of platform (GitHub Actions, GitLab CI, etc.)
- **Performance benchmarks**: Thresholds for walk-forward simulator speed

### Decisions Carried from Prior Phases
- **Data format**: `DD/MM/YYYY,N1,...,N20` with ascending sort (Phase 1)
- **Validation**: Format, range 1-80, count 20 per line (Phase 1)
- **Temperature control**: T ∈ [0.05, 2.0], deterministic generation (Phase 1)
- **Wheeling algorithm**: 3 juegas/volante, RD$75, ascending order, 0 duplicates (Phase 1)
- **UI structure**: 5-page Streamlit app (Phase 2)
- **Sidebar controls**: ventana móvil, pool size, boletos count, franja distribution (Phase 2)

### Quality Gate Checklist (for v1)
- [ ] `pytest tests/` passes 100%
- [ ] All statistical tests include random baseline comparison
- [ ] Theoretical floors visible in all output
- [ ] `black` formatting on all Python files
- [ ] Type hints on public functions
- [ ] Docstrings on all core modules (NumPy format)
- [ ] Import ordering consistent (stdlib → 3rd-party → local)
- [ ] Specific exception types for core errors
- [ ] SQLite database functional
- [ ] Streamlit app runs without errors
- [ ] Onboarding summary present and accurate

### Next Steps
- Proceed to `/gsd-discuss-phase 4` for Release phase
- Or capture additional quality decisions for CONTEXT.md
- Planning Phase 3 will use this CONTEXT.md as context for task decomposition
- Consider setting up `pytest` configuration and writing initial test suite

## Summary
Phase 3 Quality & Polish captures the test suite structure, quality gates, documentation standards, and deployment configuration for the SuperKinoTV application. All decisions are deterministic Python-based with full traceability, carrying forward constraints from Phases 1 (analysis) and 2 (UI). The phase enables downstream planners and executors to implement quality assurance without re-asking these decisions.