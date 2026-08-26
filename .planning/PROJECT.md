# Project: SuperKinoTV

## Overview
Streamlit-based lottery analysis application for SuperKino (Dominican Republic Keno). Analyzes historical draw data, generates number recommendations using statistical models, and provides a walk-forward simulator validated against hypergeometric baselines.

## Core Value
Deterministic statistical analysis of lottery draws without ML-based number generation — all algorithms run in Python without hallucinations.

## Current State — v1.0 Shipped
**Shipped:** August 2026 (milestone v1.0 MVP)

The following has been shipped:
- Codebase map (.planning/codebase/ with 7 files: STACK.md through CONCERNS.md)
- Planning artifacts (PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md)
- Onboarding summary (.planning/onboarding/SUMMARY.md)
- Four phase CONTEXT.md files (Phases 1-4)
- Deterministic Python analysis engine (Phase 1)
- Streamlit UI (5 pages, Phase 2)
- Test suite structure and quality gates (Phase 3)
- Release criteria and documentation (Phase 4)

**Product Goals (still valid):**
- Provide statistical analysis of historical lottery draws
- Offer number generation with temperature-controlled randomness
- Validate results against theoretical hypergeometric distributions
- Enable walk-forward backtesting to compare user results vs random baseline

**Target Audience (still valid):**
- Lottery enthusiasts interested in statistical analysis
- Users who want to compare their number selections against random baselines

**Success Metrics (update planned for v1.1):**
- Number of active users analyzing draws
- User satisfaction with prediction quality
- Accuracy of hypergeometric baseline comparisons

## Constraints
- Data: 120 historical draws from April 2026 to August 2026
- Technology: Python 3.11+, Streamlit, pandas, numpy, scipy, plotly
- No real-time draw tracking; offline analysis only

## Next Milestone Goals — v1.1
- Set up CI/CD pipeline
- Write formal test suite (pytest coverage)
- Optimize temperature parameter tuning
- Mobile responsiveness for Streamlit pages
- User feedback collection mechanism
- Maintenance schedule and versioning strategy
- Database re-seeding documentation

## Key Decisions (archived in milestones)
- **Data format:** DD/MM/YYYY,N1,...,N20 with ascending sort (v1.0)
- **Validation:** Format pattern, range 1-80, exactly 20 numbers/line (v1.0)
- **Temperature:** T ∈ [0.05, 2.0] softmax distribution (v1.0)
- **Wheeling:** 3 juegas per volante, RD$75 cost, ascending order, 0 duplicates (v1.0)
- **UI:** 5-page Streamlit app with sidebar controls (v1.0)
- **Quality:** Honest statistics, random baseline mandatory (v1.0)
- **Language:** Spanish discussion in Phase 1 (v1.0)

## Evolution
This document evolves at milestone boundaries.

**After v1.0 milestone:**
- Moved requirements FR-1 through FR-7 to Validated section
- Added Q-1 and NF-5 to Active for v1.1
- Documented technical debt items for future work
- Updated constraints and next milestone goals

**Current:** After v1.0 milestone completion, preparing v1.1 planning.