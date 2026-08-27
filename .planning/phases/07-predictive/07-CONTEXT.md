# Phase 7: Predictive Analysis & Optimization — Context

**Date:** 2026-08-27

## Domain
Intelligent analysis to optimize number selection with suggested distributions and predictive insights. Comprehensive analysis combining all available data factors.

## Decisions

### Tipo de Análisis
- **Comprehensive:** Combine ALL available factors for prediction
- Frequency analysis (which numbers appear most/least)
- Gap analysis (draws since last appearance per number)
- Co-ocurrence analysis (which numbers appear together)
- Temperature-weighted scoring (recent trends weighted higher)
- Temporal patterns (day-of-week, monthly cycles if detectable)
- Band distribution trends (which bands are hot/cold)

### Sugerencias de Distribución
- **Ambas + más:** Frequency + trends + temporal patterns
- Historical frequency: if Baja appears more often, suggest more Baja
- Trend detection: identify when a band is gaining/losing frequency
- Temporal patterns: detect cyclical behavior in band distributions
- Suggested distributions based on combined analysis

### Presentación de Resultados
- **Ambos:** Dashboard visual + sección de detalle expandible
- **Dashboard:** Confidence metrics cards, trend charts, scoring tables
- **Detail sections:** Expandable sections with analysis justification
- Number scoring: each number gets a confidence score (0-100)
- Band distribution suggestion with confidence level
- Recommended ticket compositions with reasoning

## Canonical References
- `app.py:144-228` — Existing analysis functions (frequency, gap, co-occurrence)
- `app.py:229-320` — `compute_frequency_ranking()` and `generate_dynamic_pool()`
- `app.py:1040-1070` — `render_tab_tickets()` (reference for tab structure)

## Code Context
- **Reusable:** All existing analysis functions (frequency, gap, co-occurrence, band metrics)
- **New code required:** Predictive scoring engine, suggestion algorithm, visualization
- **Integration point:** New `render_tab_predictive()` function, add to `main()` tab list
- **Pattern:** Follow existing analysis function patterns for consistency

## Deferred Ideas
- (none)
