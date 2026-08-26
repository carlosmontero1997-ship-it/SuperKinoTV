# Integrations

## Database
- `sqlite3` (stdlib) — `data/superkino.db`
- Database re-seeded from `SuperKinoTV.txt` on fresh start
- No external database systems required

## UI Framework
- `streamlit>=1.35.0` — primary UI framework
- App runs with: `streamlit run superkino/app/Home.py`

## Testing
- `pytest` — test runner
- Test suite located at `tests/test_core.py`
- Tests cover core analysis functions without Streamlit dependencies

## Data Input
- `SuperKinoTV.txt` — historical lottery data file
  - Format: `DD/MM/AAAA,n1,n2,...,n20` per line
  - 120 draws from 21/04/2026 to 19/08/2026
  - Parsed by `ingest.py` validator

## External Dependencies
- `plotly>=5.18.0` — interactive visualizations in analysis pages
- `numpy>=1.26.0` — numerical operations in core analysis
- `pandas>=2.2.0` — data manipulation in ingest and analysis

## Build/Deployment
- No build step; pure Python application
- Dependencies installed via `pip install -r requirements.txt` or `poetry install`
- Entry point: `streamlit run superkino/app/Home.py`