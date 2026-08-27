# Roadmap: SuperKinoTV v1.1

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-08-26)
- ◆ **v1.1 Keno Analysis & Wheeling** — Phases 1-4 (current)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-08-26</summary>

- [x] Phase 1: Core Analysis Engine (2/2 plans) — completed 2026-08-26
- [x] Phase 2: Streamlit UI (2/2 plans) — completed 2026-08-26
- [x] Phase 3: Quality & Polish (2/2 plans) — completed 2026-08-26
- [x] Phase 4: Release (2/2 plans) — completed 2026-08-26

</details>

<details open>
<summary>◆ v1.1 Keno Analysis & Wheeling (Phases 1-4) — CURRENT</summary>

### Phase 1: Data Ingestion & Controls ✅

**Goal:** User can upload/paste historical Keno data and configure all analysis parameters via sidebar controls.

**Requirements:** DATA-01 through DATA-05, CTRL-01 through CTRL-04

**Plans:** 2/2 plans completed

Plans:
- [x] 01-01-PLAN.md — Strict data ingestion with dual source detection, replace confirmation, session state persistence
- [x] 01-02-PLAN.md — Sidebar controls with forced Personalizada band distribution, auto-recalc, sum validation, colored metrics

**Success Criteria:**
1. User can upload .txt/.csv file or paste data into text area — both produce valid draws
2. System parses DD/MM/YYYY,N1,...,N20 format and sorts numbers ascending
3. Sidebar sliders control window (max 100), pool size (15-30), ticket count (6-30)
4. Band distribution is always Personalizada (forced, no presets) with auto-recalc on pool size change
5. Invalid lines are rejected with numbered error messages — all-or-nothing (any error blocks all data)

**UI hint:** yes

### Phase 2: Analysis Matrices & Pool Generation ✅

**Goal:** Display intermediate frequency matrices and generate ranked dynamic pool from statistical analysis.

**Requirements:** MATX-01, MATX-02, POOL-01, POOL-02

**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Matrix tab: conditional formatting, gap analysis, positional frequency totals
- [x] 02-02-PLAN.md — Pool tab: full 80-number ranking, band colors, gap context, co-occurrence display

**Success Criteria:**
1. 100×20 intermediate matrix displays all draws with 20 sorted positions
2. 10×10 positional frequency matrix groups numbers by adjacent lane pairs
3. Dynamic pool generated from deduplicated frequency + co-occurrence ranking
4. Pool shows band metrics (Low/Mid/High counts matching selected distribution)

**UI hint:** yes

### Phase 3: Wheeling, Volantes & Ticket Verification ✅

**Goal:** Generate deterministically reduced ticket sets, organize into physical volantes, and verify against winning numbers.

**Requirements:** TICK-01 through TICK-06

**Plans:** pending

**Success Criteria:**
1. Wheeling algorithm produces deterministic reduced combinations from pool
2. Tickets grouped into volantes of 3 plays each with RD$75 cost display
3. Strict blindaje enforced: 0 out-of-pool numbers, ascending sort, 0 duplicates
4. Download button exports all generated tickets as .txt file
5. All tickets are unique (no permutations or duplicates)
6. User can input winning numbers and see aciertos (matches) per ticket with prize calculation

**UI hint:** yes

### Phase 4: Walk-Forward Backtesting

**Goal:** Execute walk-forward backtest comparing user's wheeling strategy against random baseline.

**Requirements:** BT-01 through BT-05

**Plans:** pending

**Success Criteria:**
1. Walk-forward simulation: train on N draws, test on next draw, slide forward
2. User's strategy performance tracked across all test periods
3. Random baseline (hypergeometric) comparison displayed
4. Temperature parameter T controls exploration vs exploitation
5. Results visualization: cumulative aciertos, hit rate, ROI comparison

**UI hint:** yes

</details>

### Backlog

No backlog items — all v1.1 phases defined.

---
*Last updated: 2026-08-27 after Phase 3 verification*
