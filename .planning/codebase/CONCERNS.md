# Known Concerns and Open Questions

## Performance
- Walk-forward simulator may be slow with large backtest windows
- Hypergeometric reference computation is computationally intensive

## Numerical Stability
- Temperature parameter T in [0.05, 2.0] range requires careful handling
- Very small probabilities may underflow in probability calculations

## Data Quality
- Input format strictly validated: `DD/MM/AAAA,n1,n2,...,n20`
- Missing or malformed lines in `SuperKinoTV.txt` may cause parser errors
- Database re-seeding may lose prior analysis results

## UI Limitations
- Streamlit page reload resets slider and control state
- Large plotly visualizations may be slow on low-resolution displays
- No client-side state persistence beyond session

## Scope
- Current scope: lottery analysis for SuperKino (Dominican Republic Keno)
- Non-goals: real-time draw tracking, external lottery integration, mobile app
- Future considerations: extended number ranges, additional statistical tests, user authentication for result saving