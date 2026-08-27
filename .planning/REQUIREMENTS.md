# Requirements: SuperKinoTV v1.1

**Defined:** 2026-08-26
**Core Value:** Deterministic combinatorial analysis and wheeling-based ticket generation from historical Keno 20/80 data

## v1 Requirements

### Data Ingestion

- [ ] **DATA-01**: User can upload .txt or .csv file with historical draw data
- [ ] **DATA-02**: User can paste draw data directly into a text area
- [ ] **DATA-03**: System parses DD/MM/YYYY,N1,...,N20 format per line
- [ ] **DATA-04**: System sorts 20 numbers per draw ascending (low to high)
- [ ] **DATA-05**: System validates numbers in range 1-80 and exactly 20 unique per draw

### Controls

- [ ] **CTRL-01**: Sidebar slider for sliding window (max 100 retroactive draws)
- [ ] **CTRL-02**: Sidebar slider for dynamic pool size (15-30, default 20)
- [ ] **CTRL-03**: Sidebar slider for ticket quantity (6-30, default 18)
- [ ] **CTRL-04**: Sidebar selector for band distribution (Low/Mid/High preset or custom)

### Matrices Tab

- [ ] **MATX-01**: Display 100×20 intermediate matrix (sorted draws × positions)
- [ ] **MATX-02**: Display 10×10 positional frequency matrix grouped by adjacent lane pairs (C1=B1-B2, ..., C10=B19-B20)

### Pool Tab

- [ ] **POOL-01**: Generate dynamic pool of N numbers from deduplicated frequency + co-occurrence ranking
- [ ] **POOL-02**: Display pool with band metrics (count in Low 01-26, Mid 27-54, High 55-80)

### Tickets Tab

- [ ] **TICK-01**: Execute deterministic wheeling reduction algorithm on dynamic pool
- [ ] **TICK-02**: Group tickets into physical volantes (3 tickets per volante)
- [ ] **TICK-03**: Display cost indicator (RD$75 per volante)
- [ ] **TICK-04**: Enforce strict blindaje: 0 numbers outside pool, ascending sort, 0 duplicates
- [ ] **TICK-05**: Provide .txt download button for generated tickets
- [ ] **TICK-06**: Allow user to input winning numbers and verify aciertos (matches) per ticket

### Backtesting

- [ ] **BT-01**: Walk-forward simulation: train on N draws, test on next draw, slide forward
- [ ] **BT-02**: Track user's strategy performance across all test periods
- [ ] **BT-03**: Compare against random baseline (hypergeometric distribution)
- [ ] **BT-04**: Temperature parameter T controls exploration vs exploitation
- [ ] **BT-05**: Visualize results: cumulative aciertos, hit rate, ROI comparison

## v2 Requirements

### Enhanced Analysis

- **ENH-01**: Heatmap visualization of presence matrix
- **ENH-02**: Lift/co-ocurrence pair analysis tab
- **ENH-03**: Walk-forward backtesting simulator
- **ENH-04**: Temperature-controlled combination generation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time draw tracking | Offline analysis tool |
| ML/AI number prediction | Deterministic algorithms only |
| Mobile native app | Streamlit web app |
| User authentication | Single-user desktop tool |
| Database storage | In-memory session state |
| REST API | Streamlit UI only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 1 | Pending |
| CTRL-01 | Phase 1 | Pending |
| CTRL-02 | Phase 1 | Pending |
| CTRL-03 | Phase 1 | Pending |
| CTRL-04 | Phase 1 | Pending |
| MATX-01 | Phase 2 | Pending |
| MATX-02 | Phase 2 | Pending |
| POOL-01 | Phase 2 | Pending |
| POOL-02 | Phase 2 | Pending |
| TICK-01 | Phase 3 | Pending |
| TICK-02 | Phase 3 | Pending |
| TICK-03 | Phase 3 | Pending |
| TICK-04 | Phase 3 | Pending |
| TICK-05 | Phase 3 | Pending |
| TICK-06 | Phase 3 | Pending |
| BT-01 | Phase 4 | Pending |
| BT-02 | Phase 4 | Pending |
| BT-03 | Phase 4 | Pending |
| BT-04 | Phase 4 | Pending |
| BT-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-26*
*Last updated: 2026-08-26 after initial definition*
