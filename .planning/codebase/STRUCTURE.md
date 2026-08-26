# Code Structure

## Package Hierarchy
- `superkino` — top-level package
  - `__init__.py` — package export
  - `pyproject.toml` — project configuration
  - `requirements.txt` — dependency pins

## core/ — Analysis Engine
- `models.py` — Data models (Draw, DrawHistory) with validation
- `ingest.py` — Line parsing, validation, gap detection
- `analysis.py` — Mathematical analysis (matrices, gaps, lift, sums/parity/decades)
- `scoring.py` — Per-number scoring, temperature-controlled generation
- `simulator.py` — Walk-forward backtest, hypergeometric reference

## app/ — Streamlit UI
- `Home.py` — Home/dashboard page
- `pages/0_Historial.py` — History display, quality report, export
- `pages/1_Analisis.py` — Analysis controls, plotly tabs
- `pages/2_Combinaciones.py` — Combination generation with weight/temperature
- `pages/3_Simulador.py` — Simulator execution, walk-forward backtest

## tests/ — Test Suite
- `test_core.py` — Core module tests (unit tests for models, ingest, analysis, scoring)

## Data
- `SuperKinoTV.txt` — Historical draw data (120 draws, 21/04/2026 – 19/08/2026)
- `data/superkino.db` — SQLite database (generated, not versioned)

## Entry Point
- Streamlit app launched via `streamlit run superkino/app/Home.py`