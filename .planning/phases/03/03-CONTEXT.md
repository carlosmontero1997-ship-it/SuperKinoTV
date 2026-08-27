# Phase 3 Enhancement: Ticket Verification — Context

**Gathered:** 2026-08-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Add ability for user to input winning numbers and verify how many matches (aciertos) each generated ticket has. This is an enhancement to the existing Phase 3 wheeling/volantes functionality.

</domain>

<decisions>
## Implementation Decisions

### Input Method
- **D-01:** User inputs 20 winning numbers via text area (same format as historical data: DD/MM/YYYY,N1,...,N20)
- **D-02:** Alternative: simple text input with comma-separated numbers (no date required for verification)
- **D-03:** Winning numbers validated: 20 unique numbers in range 1-80

### Verification Display
- **D-04:** Each ticket shows aciertos count (0-10 matches)
- **D-05:** Matching numbers highlighted in green within each ticket
- **D-06:** Summary: total aciertos, best ticket, distribution of aciertos (how many tickets got 5+, 6+, 7+, etc.)

### Prize Calculation (Optional)
- **D-07:** Display prize tiers based on Dominican Republic Keno 20/80 rules:
  - 10 aciertos: Premio mayor
  - 9 aciertos: Segundo premio
  - 8 aciertos: Tercer premio
  - etc.
- **D-08:** Show estimated prize per ticket and total

### UI Location
- **D-09:** Add "Verificar Ganador" section in the same "Volantes & Reduccion Combinatoria" tab, after the generated tickets
- **D-10:** Verification only available after tickets are generated (requires tickets in session state)

### OpenCode's Discretion
- Exact prize tier values (can research DR Keno rules)
- Layout of verification results
- Whether to show per-volante or per-ticket breakdown

</decisions>

<specifics>
## Specific Ideas

- User wants to quickly check if their generated tickets would have won
- The verification should be visual — easy to see which numbers matched
- Should work with any winning numbers (not just from the historical data)

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — TICK-06

### Existing Implementation
- `app.py:render_tab_tickets()` — Current volantes tab (needs enhancement)
- `app.py:wheeling_reduction()` — Current wheeling algorithm
- `app.py:group_into_volantes()` — Current volante grouping

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `render_tab_tickets()` in app.py — Current volantes rendering (line 996)
- `st.session_state.draws` — Historical draws already loaded
- Ticket generation flow: pool → wheeling → volantes → display

### Integration Points
- Tickets stored in `st.session_state` after generation
- Winning numbers input needs validation (same as historical data)
- Verification results displayed inline after ticket generation

</code_context>

---

*Phase: 03-keno-v1.1 (enhancement)*
*Context gathered: 2026-08-27*
