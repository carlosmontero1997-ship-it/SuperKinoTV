# Roadmap: SuperKinoTV v1.2

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-08-26)
- ✅ **v1.1 Keno Analysis & Wheeling** — Phases 1-3 (shipped 2026-08-26)
- 🚧 **v1.2 Backtesting & Band Distribution** — Phases 4-7 (current)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-08-26</summary>

- [x] Phase 1: Core Analysis Engine (2/2 plans) — completed 2026-08-26
- [x] Phase 2: Streamlit UI (2/2 plans) — completed 2026-08-26
- [x] Phase 3: Quality & Polish (2/2 plans) — completed 2026-08-26
- [x] Phase 4: Release (2/2 plans) — completed 2026-08-26

</details>

<details>
<summary>✅ v1.1 Keno Analysis & Wheeling (Phases 1-3) — SHIPPED 2026-08-26</summary>

- [x] Phase 1: Data Ingestion & Controls (2/2 plans) — completed 2026-08-26
- [x] Phase 2: Analysis Matrices & Pool Generation (2/2 plans) — completed 2026-08-26
- [x] Phase 3: Wheeling, Volantes & Ticket Verification (1/1 plan) — completed 2026-08-26

</details>

### 🚧 v1.2 Backtesting & Band Distribution (Phases 4-7) — CURRENT

#### Phase 4: Matrix Ordering Fix ✅

**Goal:** Ensure intermediate matrix displays S1 as most recent draw and always uses the 100 most recent draws available.

**Requirements:** MATX-03, MATX-04

**Plans:** Already implemented (no plans needed)

**Success Criteria:**
1. S1 is the top row (most recent draw) in intermediate matrix ✓
2. Matrix always uses up to 100 most recent draws (or all available if <100) ✓
3. Row numbering is consistent across the app ✓

**UI hint:** no

#### Phase 5: Dynamic Band Distribution per Ticket ✅

**Goal:** User can select band distribution scheme (4-3-3, 3-4-3, 1-4-4-1, etc.) and wheeling algorithm respects it per ticket.

**Requirements:** BAND-01, BAND-02, BAND-03

**Plans:** 1 plan

Plans:
- [x] 05-01-PLAN.md — Add per-ticket band distribution selector, wheeling with band filtering, and per-ticket band display

**Success Criteria:**
1. Sidebar shows band distribution selector with common presets + custom option ✓
2. Wheeling algorithm produces tickets matching selected distribution ✓
3. Ticket summary shows band composition per ticket ✓
4. Band distribution info visible in volantes display ✓

**UI hint:** yes

#### Phase 6: Walk-Forward Backtesting Engine ✅

**Goal:** Execute walk-forward backtest comparing user's wheeling strategy against random baseline with temperature control.

**Requirements:** BT-01, BT-02, BT-03, BT-04, BT-05

**Plans:** 1 plan

Plans:
- [x] 06-01-PLAN.md — Implement walk-forward backtesting engine, hypergeometric/Monte Carlo baselines, temperature integration, and Backtesting tab UI

**Success Criteria:**
1. Walk-forward simulation runs: train on N draws, test on next, slide forward ✓
2. User strategy performance tracked across all test periods ✓
3. Random baseline comparison displayed (hypergeometric + Monte Carlo) ✓
4. Temperature parameter T controls exploration vs exploitation ✓
5. Results visualization: cumulative aciertos, hit rate, ROI comparison ✓

**UI hint:** yes

#### Phase 7: Predictive Analysis & Optimization

**Goal:** Intelligent analysis to optimize number selection with suggested distributions and predictive insights.

**Requirements:** BT-06

**Plans:** 1 plan

Plans:
- [ ] 07-01-PLAN.md — Implement predictive analysis engine, number scoring, distribution suggestions, and Predictive Analysis tab

**Success Criteria:**
1. Predictive analysis suggests optimal number combinations
2. Distribution suggestions based on historical patterns
3. Intelligent analysis combines frequency, gap, and co-occurrence data
4. Results displayed with clear confidence indicators

**UI hint:** yes

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Core Analysis Engine | v1.0 | 2/2 | Complete | 2026-08-26 |
| 2. Streamlit UI | v1.0 | 2/2 | Complete | 2026-08-26 |
| 3. Quality & Polish | v1.0 | 2/2 | Complete | 2026-08-26 |
| 4. Release | v1.0 | 2/2 | Complete | 2026-08-26 |
| 1. Data Ingestion & Controls | v1.1 | 2/2 | Complete | 2026-08-26 |
| 2. Analysis Matrices & Pool | v1.1 | 2/2 | Complete | 2026-08-26 |
| 3. Wheeling, Volantes & Verification | v1.1 | 1/1 | Complete | 2026-08-26 |
| 4. Matrix Ordering Fix | v1.2 | 0/1 | Not started | - |
| 5. Band Distribution per Ticket | v1.2 | 1/1 | Complete | 2026-08-27 |
| 6. Walk-Forward Backtesting | v1.2 | 1/1 | Complete | 2026-08-27 |
| 7. Predictive Analysis | v1.2 | 0/1 | Not started | - |

### Backlog

No backlog items.

---
*Last updated: 2026-08-27 after v1.2 milestone start*
