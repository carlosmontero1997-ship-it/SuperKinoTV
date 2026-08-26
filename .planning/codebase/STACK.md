# Stack Overview

## Language & Runtime
- Python 3.11+ with `requires-python = ">=3.11"` in pyproject.toml

## Key Packages
- `streamlit>=1.35.0` — web application framework for the UI
- `pandas>=2.2.0` — data manipulation and analysis
- `numpy>=1.26.0` — numerical computing
- `scipy>=1.12.0` — statistics (hypergeometric distribution)
- `plotly>=5.18.0` — interactive visualizations

## Project Structure
```
superkino/
├── core/           # Pure Python analysis (testable without Streamlit)
│   ├── models.py   # Draw dataclass + DrawHistory with validation
│   ├── ingest.py   # Line parser + validator + gap detection
│   ├── analysis.py # Presence/positional matrices, gaps, lift, sums/parity/decades
│   ├── scoring.py  # Individual number scores + temperature generation
│   └── simulator.py # Walk-forward backtest + hypergeometric reference
├── app/            # Streamlit UI layer
│   ├── Home.py                 # Home page
│   └── pages/
│       ├── 0_Historial.py      # History: upload, quality report, table, export
│       ├── 1_Analisis.py       # Analysis: sliders, plotly tabs
│       ├── 2_Combinaciones.py  # Combinations: weight/temperature controls
│       └── 3_Simulador.py      # Simulator: walk-forward backtest execution
├── tests/          # pytest test suite (test_core.py)
├── requirements.txt # Pinned dependencies
├── pyproject.toml   # Project config, dependencies, entry point
└── SuperKinoTV.txt  # Historical lottery data
```

## Persistence
- SQLite stdlib via `data/superkino.db` (not versioned; re-seeded from `SuperKinoTV.txt` on fresh start)