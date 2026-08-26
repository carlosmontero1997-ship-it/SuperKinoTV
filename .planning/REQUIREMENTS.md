# Requirements

## Functional Requirements
- FR-1: Parse historical draw data from `SuperKinoTV.txt` format `DD/MM/AAAA,n1,n2,...,n20`
- FR-2: Validate draw data for correct format and number ranges
- FR-3: Generate presence/positional matrices for each draw
- FR-4: Calculate gap statistics (frequency, last seen, lift)
- FR-5: Implement temperature-controlled number generation (softmax, T ∈ [0.05, 2.0])
- FR-6: Walk-forward backtest simulator with hypergeometric reference comparison
- FR-7: Interactive Streamlit UI with tabs for analysis, combinations, and simulator

## Non-Functional Requirements
- NF-1: Must be testable without Streamlit dependencies (core modules only)
- NF-2: All statistical comparisons must include random baseline
- NF-3: Theoretical floors always visible in output
- NF-4: Python 3.11+ compatibility
- NF-5: SQLite persistence for computed results

## Open Questions
- Q-1: Optimal temperature parameter range for number generation
- Q-2: Whether to include user result comparison in the core module or UI layer
- Q-3: Frequency of database re-seeding from source data