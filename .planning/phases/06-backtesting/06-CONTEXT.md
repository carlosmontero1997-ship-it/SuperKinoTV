# Phase 6: Walk-Forward Backtesting Engine — Context

**Date:** 2026-08-27

## Domain
Execute walk-forward backtest comparing user's wheeling strategy against random baseline with temperature control. Completely new feature — no existing code.

## Decisions

### UI Location
- **Nueva pestaña "Backtesting"** — 4th tab in the Streamlit app
- Tab order: Matrices → Pool → Volantes → Backtesting
- New function: `render_tab_backtesting(draws, config)`

### Parámetros Walk-Forward
- **Ventana fija + sliders:** Train on N draws (configurable), test on 1 draw, slide forward by 1
- Default training window: 80 draws (adjustable via slider, range 20-100)
- Test period: always 1 draw (the next draw after training window)
- Step size: always 1 (slide by 1 draw each iteration)
- Walk-forward runs until no more test draws available

### Control de Temperatura
- **Ambos:** Sidebar slider T (0.05-2.0) + override in backtesting tab
- Sidebar T is the default for all generation
- Backtesting tab has its own T slider that overrides sidebar T for backtesting runs only
- T affects number selection probability distribution (higher T = more random, lower T = more deterministic/frequent numbers)

### Línea Base Random
- **Ambas:** Hypergeometric exacta + Monte Carlo simulation
- **Hypergeometric:** Mathematical probability of k successes when drawing 20 from 80, given player's 10 numbers
- **Monte Carlo:** Run 1000 random simulations per test period, compare averages
- Both displayed side-by-side with user's strategy results

### Visualización
- **Cumulative aciertos chart:** Line chart showing user strategy vs random baseline over time
- **Hit rate comparison:** Metric cards showing hit rate for user vs random
- **ROI comparison:** Cost (RD$75 per volante × number of volantes) vs prizes won
- **Temperature effect:** Show how different T values affect performance

## Canonical References
- `app.py:325-404` — `wheeling_reduction()` (needs temperature parameter)
- `app.py:1040-1070` — `render_tab_tickets()` (reference for tab structure)
- `app.py:1391-1395` — `main()` tab layout (add 4th tab)

## Code Context
- **New code required:** No existing backtesting implementation
- **Reusable:** Pool generation, wheeling algorithm, band distribution from Phase 5
- **Integration point:** New `render_tab_backtesting()` function, add to `main()` tab list
- **Dependencies:** scipy.stats for hypergeometric distribution (already in requirements.txt)

## Deferred Ideas
- (none)
