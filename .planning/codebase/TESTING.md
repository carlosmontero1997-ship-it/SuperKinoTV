# Testing

## Test Framework
- `pytest` — test runner (configured in pyproject.toml)
- Test files located in `tests/` directory

## Test Coverage
- `tests/test_core.py` — Core module tests
  - Model validation and dataclass tests
  - Ingest parser/validator tests
  - Analysis function tests (matrices, gaps, lift)
  - Scoring and temperature generation tests
  - Simulator backtest tests with hypergeometric reference

## Running Tests
```bash
pytest tests/
# or with coverage
pytest --cov=superkino tests/
```

## Test Philosophy
- Core modules (`core/`) tested without Streamlit dependencies
- Integration of core → UI tested manually via the running app
- Hypergeometric baseline comparison always included in test assertions
- Temperature generation tested across range [0.05, 2.0]

## Continuous Integration
- No CI configured yet; tests run locally via `pytest`