# Phase 2: Streamlit UI — Context Decisions

## Domain
This phase implements the Streamlit user interface layer for SuperKino (Dominican Republic Keno) lottery analysis application. It provides the web-based UI for data input, analysis, number generation, and simulator execution. All UI elements are driven by deterministic Python logic without LLM-generated interfaces.

## Core Value
Deterministic Streamlit UI for lottery analysis — all visual elements, controls, and interactions are implemented in Python with full determinism, no model-based UI generation.

## Decisions Captured

### UI Architecture
- **5-page Streamlit app** with clear separation of concerns:
  - Page 1: Home — dashboard overview, quick data upload
  - Page 2: Historial — historical draw table, quality report, export
  - Page 3: Analisis — matrix displays, slider controls, frequency analysis
  - Page 4: Combinaciones — wheeling algorithm output, volante generation
  - Page 5: Simulador — walk-forward backtest, hypergeometric comparison

### Page Structure
- **Home.py**: Dashboard overview, key statistics, quick data upload/paste, summary metrics
- **0_Historial.py**: Historical draw table with search/filter, quality report generation, data export functionality, upload validation feedback
- **1_Analisis.py**: Slider controls (ventana móvil, pool size, boletos count), distribution franja selectors (Baja/Media/Alta), mobile matrix 100×20 display, positional matrix 10×10 (C1=B1-B2, ..., C10=B19-B20), frequency calculations
- **2_Combinaciones.py**: Wheeling algorithm output, 3 juegas per volante, RD$75 per volante, dynamic pool generation from frequency ranking, strict ascending number order within each ticket, 0 duplicated/permuted tickets guarantee
- **3_Simulador.py**: Walk-forward backtest execution, hypergeometric reference comparison, user results vs random baseline visualization, temperature parameter control T ∈ [0.05, 2.0]

### Sidebar Controls (Phase 1 decisions carried forward)
- **Ventana móvil slider**: Max 100 sorteos retroactivos desde sorteo seleccionado
- **Tamaño pool dinámico slider**: 15-30 números, valor por defecto 20
- **Cantidad de boletos slider**: 6-30 boletos, valor por defecto 18
- **Distribución por franja**: 
  - 4-3-3 (Baja 01-26, Media 27-54, Alta 55-80)
  - 3-4-3
  - 3-3-4
  - Personalizada (manual selection)

### UI Determinism Constraints
- **0 numbers outside the dynamic pool**: All generated numbers must come from the dynamically ranked pool
- **Strict ascending order**: Numbers always sorted menor a mayor within each ticket
- **0 duplicated/permuted tickets**: Each volante must have unique, non-permuted combinations
- **Honest statistics**: Theoretical floors always visible in output
- **Random baseline comparison**: Mandatory comparison against random expectation in all displays
- **Temperature parameter**: T ∈ [0.05, 2.0] visible and controllable in simulator

### Data Flow
1. **Input**: Upload .txt/.csv file or paste historial directly (format: DD/MM/YYYY,N1,N2,...,N20)
2. **Validation**: Format validation, range 1-80, exactly 20 numbers per line
3. **Processing**: Ascending sort, mobile matrix 100×20, positional matrix 10×10
4. **Analysis**: Gap statistics, frequency calculations, lift computations
5. **Generation**: Temperature-controlled softmax, dynamic pool ranking, wheeling algorithm
6. **Output**: Streamlit display with all results, comparisons, and export options

### UI-Code Integration
- **Core layer** (`superkino/core/`): Pure Python analysis, no Streamlit imports
- **UI layer** (`superkino/app/`): Streamlit-specific components, depends on core layer
- **Data persistence**: SQLite (`data/superkino.db`) for computed results, re-seeded from source data
- **Entry point**: `streamlit run superkino/app/Home.py`

### Key UI Components
- **Plotly visualizations**: Interactive charts in Analisis and Simulador pages
- **Slider controls**: Range inputs for ventana móvil, pool size, boletos count
- **Distribution franja selectors**: Manual selection of Baja/Media/Alta number distribution
- **Table displays**: Historical draws, frequency matrices, generated combinations
- **Export functionality**: Download generated tickets as .txt file
- **Quality report**: Generated analysis summary with statistics

### Canonical References
- `.planning/codebase/STACK.md` — Python 3.11+, Streamlit 1.35.0, pandas, numpy, scipy, plotly
- `.planning/codebase/ARCHITECTURE.md` — Core/UI layering strategy, data flow
- `.planning/codebase/STRUCTURE.md` — Package hierarchy, page locations
- `.planning/codebase/INTEGRATIONS.md` — Streamlit + SQLite integration, database re-seeding
- `.planning/codebase/CONVENTIONS.md` — Streamlit naming conventions, snake_case for functions/variables
- `.planning/codebase/TESTING.md` — Streamlit test framework, pytest for core modules
- `.planning/codebase/CONCERNS.md` — UI performance, data quality, numerical stability concerns

### Open Questions / Deferred
- **Temperature parameter display**: Optimal way to show and control T ∈ [0.05, 2.0] in UI
- **Database re-seeding**: Frequency and UX for re-seeding from SuperKinoTV.txt
- **User result comparison**: Whether to include in core module or UI layer
- **Extended number ranges**: Visualization beyond 1-80 if needed
- **Mobile responsiveness**: Streamlit page layout for different screen sizes
- **Download format**: .txt export format for generated tickets (beyond 3 juegas/volante)

### Decisions Carried from Phase 1
- Data ingestion format: `DD/MM/YYYY,N1,...,N20` with ascending sort
- Validation: format, range 1-80, count 20 per line
- Mobile matrix 100×20 and positional matrix 10×10
- Temperature-controlled generation T ∈ [0.05, 2.0]
- Wheeling algorithm: 3 juegas/volante, RD$75, ascending order, 0 duplicates
- Sidebar controls: ventana móvil max 100, pool 15-30, boletos 6-30, franja distribution

## Next Steps
- Proceed to `/gsd-discuss-phase 3` for Quality & Polish phase
- Or capture additional UI design decisions for CONTEXT.md
- Planning Phase 2 will use this CONTEXT.md as context for task decomposition