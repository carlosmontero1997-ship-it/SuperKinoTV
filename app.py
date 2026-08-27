"""
SuperKinoTV — Keno 20/80 Analysis & Ticket Generator
=====================================================
Streamlit WebApp for deterministic analysis and wheeling-based ticket generation.

100% deterministic — all algorithms run in Python backend.
No LLM/ML number generation.
"""

from __future__ import annotations

import io
import itertools
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats as sp_stats

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SuperKinoTV — Keno 20/80",
    page_icon="🎰",
    layout="wide",
)

BAND_LOW = list(range(1, 27))    # 01-26
BAND_MID = list(range(27, 55))   # 27-54
BAND_HIGH = list(range(55, 81))  # 55-80

COST_PER_VOLANTE = 75  # RD$

# Per-ticket band distribution presets (B-M-A counts that sum to 10)
# Phase 5: BAND-01 — user selects a scheme from sidebar
TICKET_BAND_PRESETS = {
    "4-3-3": (4, 3, 3),
    "3-4-3": (3, 4, 3),
    "3-3-4": (3, 3, 4),
    "1-4-5": (1, 4, 5),
    "2-4-4": (2, 4, 4),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Draw:
    date_iso: str
    numbers: Tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.numbers) != 20:
            raise ValueError("Un sorteo debe tener exactamente 20 numeros.")
        if not all(1 <= n <= 80 for n in self.numbers):
            raise ValueError("Los numeros deben estar en el rango 1-80.")
        if len(set(self.numbers)) != 20:
            raise ValueError("Los numeros deben ser unicos.")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA INGESTION
# ═══════════════════════════════════════════════════════════════════════════════

def parse_line(raw: str) -> Tuple[bool, Optional[Draw], Optional[str]]:
    """Parse a single line: DD/MM/YYYY,N1,...,N20. Returns (ok, draw, error_msg)."""
    raw = raw.strip()
    if not raw:
        return False, None, "Linea vacia."

    parts = raw.split(",")
    if len(parts) != 21:
        return False, None, "Formato invalido: se esperan 21 campos (1 fecha + 20 numeros)."

    date_str = parts[0].strip()
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        date_iso = dt.strftime("%Y-%m-%d")
    except ValueError:
        return False, None, f"Fecha invalida: '{date_str}'. Use DD/MM/AAAA."

    try:
        nums = [int(p.strip()) for p in parts[1:]]
    except ValueError:
        return False, None, "Todos los valores deben ser enteros."

    if len(nums) != 20:
        return False, None, f"Se esperan 20 numeros, se encontraron {len(nums)}."
    if not all(1 <= n <= 80 for n in nums):
        return False, None, "Los numeros deben estar en el rango 1-80."
    if len(set(nums)) != 20:
        return False, None, "Los numeros deben ser unicos dentro del sorteo."

    sorted_nums = tuple(sorted(nums))
    return True, Draw(date_iso=date_iso, numbers=sorted_nums), None


def ingest_lines(lines: List[str]) -> Tuple[List[Draw], List[Tuple[int, str, str]]]:
    """Parse multiple lines. Returns (draws, errors).
    
    Per D-02: if ANY line fails, NO data is loaded (all-or-nothing).
    Errors tuple: (line_number, error_message, raw_line_content)
    """
    draws: List[Draw] = []
    errors: List[Tuple[int, str, str]] = []
    seen_dates: set = set()

    for idx, raw in enumerate(lines):
        ok, draw, err = parse_line(raw)
        if not ok:
            errors.append((idx + 1, err, raw.strip()))  # 1-indexed line numbers per D-03
            continue
        if draw.date_iso in seen_dates:
            errors.append((idx + 1, f"Fecha duplicada: {draw.date_iso}", raw.strip()))
            continue
        seen_dates.add(draw.date_iso)
        draws.append(draw)

    # D-02: all-or-nothing — if ANY errors, return no draws
    if errors:
        return [], errors

    draws.sort(key=lambda d: d.date_iso)
    return draws, errors


def get_draws_from_input(uploaded_file, text_area: str) -> Tuple[List[Draw], List[Tuple[int, str, str]]]:
    """Unified ingestion from file upload or text area."""
    all_lines: List[str] = []

    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8", errors="replace")
        all_lines.extend(content.splitlines())

    if text_area.strip():
        all_lines.extend(text_area.strip().splitlines())

    return ingest_lines(all_lines)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ALGORITHMS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_intermediate_matrix(draws: List[Draw], window: int) -> pd.DataFrame:
    """100x20 intermediate matrix: each row is a draw, columns are sorted positions.
    
    S1 = most recent draw, S2 = second most recent, etc.
    """
    subset = draws[-window:] if len(draws) >= window else draws
    subset_reversed = list(reversed(subset))  # S1 = most recent
    rows = []
    for d in subset_reversed:
        rows.append(list(d.numbers))
    df = pd.DataFrame(rows, columns=[f"P{i+1}" for i in range(20)])
    df.index = [f"S{i+1}" for i in range(len(subset_reversed))]
    return df


def compute_positional_frequency_matrix(draws: List[Draw], window: int) -> pd.DataFrame:
    """10x10 positional frequency matrix grouped by adjacent lane pairs.

    Columns: C1=(B1,B2), C2=(B3,B4), ..., C10=(B19,B20)
    Rows: frequency bands or positional groups.

    For each pair of adjacent positions (col j, col j+1), we count how many
    numbers from each band appear in that pair across all draws in the window.
    """
    subset = draws[-window:] if len(draws) >= window else draws

    # 10 column groups: C_k covers positions (2k-1, 2k) for k=1..10
    # For each draw and each column group, count numbers in each band
    band_labels = ["Baja(01-26)", "Media(27-54)", "Alta(55-80)"]
    col_labels = [f"C{i+1}" for i in range(10)]

    # Matrix: 3 bands x 10 column groups
    matrix = np.zeros((3, 10), dtype=int)

    for draw in subset:
        nums = draw.numbers
        for col_group in range(10):
            pos_a = col_group * 2      # 0-indexed position
            pos_b = col_group * 2 + 1
            for pos in [pos_a, pos_b]:
                if pos < len(nums):
                    n = nums[pos]
                    if n in BAND_LOW:
                        matrix[0][col_group] += 1
                    elif n in BAND_MID:
                        matrix[1][col_group] += 1
                    else:
                        matrix[2][col_group] += 1

    df = pd.DataFrame(matrix, index=band_labels, columns=col_labels)
    return df


def compute_gap_analysis(draws: List[Draw], window: int) -> pd.DataFrame:
    """Gap analysis: number of draws since each number last appeared.

    Returns DataFrame with columns ['Numero', 'Ultima_Aparicion', 'Gap'],
    sorted by Gap descending (coldest numbers first).
    Numbers that never appeared in the window get gap = window.
    """
    subset = draws[-window:] if len(draws) >= window else draws
    n_draws = len(subset)

    last_seen: Dict[int, int] = {}
    for idx, draw in enumerate(subset):
        for n in draw.numbers:
            last_seen[n] = idx

    rows: List[Dict] = []
    for num in range(1, 81):
        if num in last_seen:
            gap = n_draws - 1 - last_seen[num]
            last_date = subset[last_seen[num]].date_iso
        else:
            gap = n_draws
            last_date = "N/A"
        rows.append({"Numero": num, "Ultima_Aparicion": last_date, "Gap": gap})

    df = pd.DataFrame(rows)
    df = df.sort_values("Gap", ascending=False).reset_index(drop=True)
    df.index = range(1, len(df) + 1)
    df.index.name = "Rank"
    return df


def compute_frequency_ranking(draws: List[Draw], window: int) -> List[Tuple[int, float, int]]:
    """Rank numbers by frequency + co-occurrence score.

    Returns sorted list of (number, score, frequency) descending by score.
    Score = frequency + lambda * mean_cooccurrence_with_top
    """
    subset = draws[-window:] if len(draws) >= window else draws

    # Frequency count
    freq = Counter()
    for draw in subset:
        for n in draw.numbers:
            freq[n] += 1

    # Co-occurrence: for each number, average co-occurrence with all other numbers
    cooc = defaultdict(float)
    n_draws = len(subset)
    for draw in subset:
        nums = list(draw.numbers)
        for i, a in enumerate(nums):
            for j, b in enumerate(nums):
                if i != j:
                    cooc[a] += 1.0

    # Normalize co-occurrence
    for n in cooc:
        cooc[n] /= max(n_draws, 1)

    # Combined score: frequency (normalized) + co-occurrence
    max_freq = max(freq.values()) if freq else 1
    max_cooc = max(cooc.values()) if cooc else 1

    scores = {}
    for n in range(1, 81):
        f_norm = freq.get(n, 0) / max_freq
        c_norm = cooc.get(n, 0) / max_cooc if max_cooc > 0 else 0
        scores[n] = f_norm + 0.3 * c_norm  # frequency weighted more

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(n, score, freq.get(n, 0)) for n, score in ranked]


def generate_dynamic_pool(
    draws: List[Draw],
    window: int,
    pool_size: int,
    band_dist: Optional[Tuple[int, int, int]],
) -> Tuple[List[int], Dict[str, int]]:
    """Generate dynamic pool of N numbers from deduplicated frequency ranking.

    Returns (pool_numbers, band_counts).
    """
    ranked = compute_frequency_ranking(draws, window)

    if band_dist is None:
        # Equilibrada Dinamica: proportional to pool_size
        low_count = math.ceil(pool_size * 26 / 80)
        mid_count = math.ceil(pool_size * 28 / 80)
        high_count = pool_size - low_count - mid_count
        if high_count < 0:
            high_count = 0
            mid_count = pool_size - low_count
        band_dist = (low_count, mid_count, high_count)

    low_n, mid_n, high_n = band_dist

    # Filter ranked numbers by band
    ranked_low = [(n, s, f) for n, s, f in ranked if n in BAND_LOW]
    ranked_mid = [(n, s, f) for n, s, f in ranked if n in BAND_MID]
    ranked_high = [(n, s, f) for n, s, f in ranked if n in BAND_HIGH]

    pool = []
    pool.extend([n for n, s, f in ranked_low[:low_n]])
    pool.extend([n for n, s, f in ranked_mid[:mid_n]])
    pool.extend([n for n, s, f in ranked_high[:high_n]])

    # If pool is smaller than requested, fill from remaining ranked numbers
    if len(pool) < pool_size:
        remaining = [n for n, s, f in ranked if n not in pool]
        pool.extend(remaining[: pool_size - len(pool)])

    pool = sorted(pool[:pool_size])

    band_counts = {
        "Baja (01-26)": sum(1 for n in pool if n in BAND_LOW),
        "Media (27-54)": sum(1 for n in pool if n in BAND_MID),
        "Alta (55-80)": sum(1 for n in pool if n in BAND_HIGH),
    }

    return pool, band_counts


# ═══════════════════════════════════════════════════════════════════════════════
# WHEELING ALGORITHM
# ═══════════════════════════════════════════════════════════════════════════════

def wheeling_reduction(
    pool: List[int],
    n_tickets: int,
    ticket_size: int = 10,
    ticket_band_dist: Optional[Tuple[int, int, int]] = None,
    uniform: bool = True,
) -> Tuple[List[Tuple[int, ...]], List[str], List[Tuple[int, int, int]]]:
    """Deterministic wheeling reduction with optional per-ticket band distribution.

    Args:
        ticket_band_dist: (baja_count, media_count, alta_count) per ticket. None = no constraint.
        uniform: If True, all tickets use same distribution. If False, wheeling may vary per ticket.

    Returns:
        (tickets, errors, ticket_band_distributions) where ticket_band_distributions[i] is the
        actual (b, m, a) count for tickets[i].
    """
    pool_sorted = sorted(pool)
    pool_size = len(pool_sorted)
    errors: List[str] = []

    if pool_size < ticket_size:
        errors.append(
            f"Pool demasiado pequeno: {pool_size} numeros < {ticket_size} requeridos. "
            f"Sube el tamano del pool o reduce la ventana."
        )
        return [], errors

    # Generate candidate combinations (only from pool numbers)
    total_combos = math.comb(pool_size, ticket_size)
    max_candidates = min(5000, total_combos)

    if max_candidates <= n_tickets:
        candidates = list(itertools.combinations(pool_sorted, ticket_size))
    else:
        step = max(1, total_combos // max_candidates)
        candidates = []
        for i, combo in enumerate(itertools.combinations(pool_sorted, ticket_size)):
            if i % step == 0:
                candidates.append(combo)
            if len(candidates) >= max_candidates:
                break

    if not candidates:
        errors.append("No se pudieron generar combinaciones con los parametros actuales.")
        return [], errors, []

    # Phase 5: Filter candidates by per-ticket band distribution
    if ticket_band_dist is not None:
        tb, tm, ta = ticket_band_dist
        filtered_candidates = []
        for combo in candidates:
            b_count = sum(1 for n in combo if n in BAND_LOW)
            m_count = sum(1 for n in combo if n in BAND_MID)
            a_count = sum(1 for n in combo if n in BAND_HIGH)
            if b_count == tb and m_count == tm and a_count == ta:
                filtered_candidates.append(combo)
        candidates = filtered_candidates
        if not candidates:
            errors.append(
                f"No se pudieron generar combinaciones con distribucion {ticket_band_dist}. "
                f"El pool no permite esta distribucion para boletos de tamano {ticket_size}."
            )
            return [], errors, []

    # Greedy coverage selection
    selected: List[Tuple[int, ...]] = []
    covered_pairs: set = set()
    ticket_bands: List[Tuple[int, int, int]] = []

    for _ in range(min(n_tickets, len(candidates))):
        best_combo = None
        best_new_pairs = -1

        for combo in candidates:
            if combo in selected:
                continue
            combo_pairs = set()
            for i in range(len(combo)):
                for j in range(i + 1, len(combo)):
                    combo_pairs.add((combo[i], combo[j]))
            new_pairs = len(combo_pairs - covered_pairs)

            if new_pairs > best_new_pairs:
                best_new_pairs = new_pairs
                best_combo = combo

        if best_combo is not None:
            selected.append(best_combo)
            # Track band distribution for this ticket
            b = sum(1 for n in best_combo if n in BAND_LOW)
            m = sum(1 for n in best_combo if n in BAND_MID)
            a = sum(1 for n in best_combo if n in BAND_HIGH)
            ticket_bands.append((b, m, a))
            for i in range(len(best_combo)):
                for j in range(i + 1, len(best_combo)):
                    covered_pairs.add((best_combo[i], best_combo[j]))
        else:
            break

    # Strict blindaje: verify all numbers are in pool, ascending, no duplicates
    result: List[Tuple[int, ...]] = []
    result_bands: List[Tuple[int, int, int]] = []
    seen: set = set()
    for idx, ticket in enumerate(selected):
        t = tuple(sorted(ticket))
        # Verify ALL numbers in pool (should always pass since candidates come from pool)
        if not all(n in pool_sorted for n in t):
            continue
        if len(t) != ticket_size:
            continue
        if t not in seen:
            seen.add(t)
            result.append(t)
            if idx < len(ticket_bands):
                result_bands.append(ticket_bands[idx])

    if len(result) < n_tickets:
        errors.append(
            f"Solo se pudieron generar {len(result)} boletos unicos de {n_tickets} solicitados."
        )

    return result[:n_tickets], errors, result_bands[:n_tickets]


def group_into_volantes(tickets: List[Tuple[int, ...]]) -> List[List[Tuple[int, ...]]]:
    """Group tickets into volantes of 3 plays each."""
    volantes = []
    for i in range(0, len(tickets), 3):
        volante = tickets[i : i + 3]
        volantes.append(volante)
    return volantes


def verify_winning_numbers(
    tickets: List[Tuple[int, ...]],
    winning_numbers: List[int],
) -> Tuple[List[Dict], Dict]:
    """Verify tickets against winning numbers.
    
    Returns (ticket_results, summary) where:
    - ticket_results: list of dicts with keys: ticket, aciertos, matching_numbers
    - summary: dict with keys: total_tickets, best_aciertos, best_tickets, distribution
    """
    if len(winning_numbers) != 20:
        raise ValueError("Se necesitan exactamente 20 numeros ganadores.")
    
    winning_set = set(winning_numbers)
    results = []
    
    for ticket in tickets:
        matching = [n for n in ticket if n in winning_set]
        results.append({
            "ticket": ticket,
            "aciertos": len(matching),
            "matching_numbers": matching,
        })
    
    results.sort(key=lambda x: x["aciertos"], reverse=True)
    
    aciertos_counts = [r["aciertos"] for r in results]
    best = max(aciertos_counts) if aciertos_counts else 0
    best_tickets = [r for r in results if r["aciertos"] == best]
    
    distribution = {}
    for threshold in [5, 6, 7, 8, 9, 10]:
        distribution[f"{threshold}+"] = len([a for a in aciertos_counts if a >= threshold])
    
    summary = {
        "total_tickets": len(tickets),
        "best_aciertos": best,
        "best_tickets": best_tickets,
        "distribution": distribution,
        "total_matches": sum(aciertos_counts),
    }
    
    return results, summary


# ═══════════════════════════════════════════════════════════════════════════════
# BACKTESTING ENGINE (Phase 6: BT-01 through BT-05)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_hypergeometric_baseline(
    ticket_numbers: Tuple[int, ...],
    drawn_numbers: Tuple[int, ...],
    pool_size: int = 80,
    draw_size: int = 20,
) -> float:
    """Compute exact hypergeometric probability of k successes.

    Uses scipy.stats.hypergeom.pmf to compute P(X=k) where:
    - X = number of ticket numbers that appear in drawn_numbers
    - pool_size = total numbers (80)
    - draw_size = numbers drawn per draw (20)
    - M = len(ticket_numbers) = numbers the player picked (10)
    """
    k = len(set(ticket_numbers) & set(drawn_numbers))
    M = len(ticket_numbers)
    return sp_stats.hypergeom.pmf(k, pool_size, draw_size, M)


def compute_hypergeometric_expected_hits(
    ticket_numbers: Tuple[int, ...],
    n_test_draws: int,
    pool_size: int = 80,
    draw_size: int = 20,
) -> List[float]:
    """Compute expected hits per test period using hypergeometric distribution.

    For each possible k (0 to len(ticket_numbers)), compute P(k) * k.
    Returns a list of expected aciertos per draw for a random player.
    """
    M = len(ticket_numbers)
    expected_per_draw = sum(
        sp_stats.hypergeom.pmf(k, pool_size, draw_size, M) * k
        for k in range(M + 1)
    )
    return [expected_per_draw * n_test_draws]


def run_monte_carlo_baseline(
    ticket_numbers: Tuple[int, ...],
    n_test_draws: int,
    n_simulations: int = 1000,
    pool_size: int = 80,
    draw_size: int = 20,
) -> Tuple[List[float], float]:
    """Run Monte Carlo simulation for random baseline.

    Each simulation draws n_test_draws random draws from pool_size.
    Returns (avg_aciertos_per_draw_list, overall_avg_hit_rate).
    """
    rng = np.random.default_rng(42)
    ticket_set = set(ticket_numbers)

    # Track aciertos per test period across all simulations
    all_aciertos = np.zeros(n_test_draws)

    for _ in range(n_simulations):
        for t in range(n_test_draws):
            drawn = rng.choice(pool_size, size=draw_size, replace=False) + 1
            drawn_set = set(drawn.tolist())
            all_aciertos[t] += len(ticket_set & drawn_set)

    avg_per_period = (all_aciertos / n_simulations).tolist()
    overall_avg = float(np.sum(all_aciertos) / (n_simulations * max(n_test_draws, 1)))
    return avg_per_period, overall_avg


def apply_temperature_to_selection(
    ranked_numbers: List[Tuple[int, float, int]],
    temperature: float,
    pool_size: int,
    band_dist: Optional[Tuple[int, int, int]],
) -> List[int]:
    """Temperature-controlled pool generation using softmax weighting.

    Converts frequency scores to selection probabilities via softmax with
    temperature T. Low T = deterministic (top scores). High T = uniform.
    """
    if temperature >= 2.0:
        # At T=2.0+, distribution approaches uniform — take top N
        return [n for n, s, f in ranked_numbers[:pool_size]]

    scores = np.array([s for _, s, _ in ranked_numbers], dtype=np.float64)

    if band_dist is not None:
        low_n, mid_n, high_n = band_dist
        low_nums = [n for n, s, f in ranked_numbers if n in BAND_LOW]
        mid_nums = [n for n, s, f in ranked_numbers if n in BAND_MID]
        high_nums = [n for n, s, f in ranked_numbers if n in BAND_HIGH]

        def _softmax_select(nums: List[int], count: int) -> List[int]:
            if not nums or count <= 0:
                return []
            num_scores = []
            for n in nums:
                for ranked_n, s, f in ranked_numbers:
                    if ranked_n == n:
                        num_scores.append(s)
                        break
                else:
                    num_scores.append(0.0)
            arr = np.array(num_scores, dtype=np.float64)
            arr = arr / max(temperature, 1e-8)
            arr -= arr.max()  # numerical stability
            probs = np.exp(arr)
            probs /= probs.sum()
            count = min(count, len(nums))
            selected = np.random.default_rng(42).choice(
                len(nums), size=count, replace=False, p=probs
            )
            return sorted(nums[i] for i in selected)

        pool = []
        pool.extend(_softmax_select(low_nums, low_n))
        pool.extend(_softmax_select(mid_nums, mid_n))
        pool.extend(_softmax_select(high_nums, high_n))

        if len(pool) < pool_size:
            remaining = [n for n, s, f in ranked_numbers if n not in pool]
            pool.extend(remaining[: pool_size - len(pool)])

        return sorted(pool[:pool_size])
    else:
        # No band constraint — softmax over all numbers
        arr = scores / max(temperature, 1e-8)
        arr -= arr.max()
        probs = np.exp(arr)
        probs /= probs.sum()
        all_nums = [n for n, s, f in ranked_numbers]
        selected = np.random.default_rng(42).choice(
            len(all_nums), size=min(pool_size, len(all_nums)),
            replace=False, p=probs,
        )
        return sorted(all_nums[i] for i in selected)


def walk_forward_backtest(
    draws: List[Draw],
    config: Dict,
    temperature: float = 1.0,
    n_tickets: int = 18,
    ticket_size: int = 10,
    mc_simulations: int = 1000,
) -> Dict:
    """Walk-forward backtesting engine.

    Train on N draws, test on next draw, slide forward by 1.
    Compares user strategy against hypergeometric and Monte Carlo baselines.
    """
    training_window = config.get("window", 80)
    pool_size = config.get("pool_size", 20)
    band_dist = config.get("band_dist")

    results = []
    cumulative_aciertos = []
    cumulative_hyper = []
    cumulative_mc = []
    total_aciertos = 0
    total_hyper = 0.0
    total_mc = 0.0

    for start in range(0, len(draws) - training_window):
        train_draws = draws[start: start + training_window]
        test_draw = draws[start + training_window]

        # Generate pool from training data
        if temperature < 2.0:
            ranked = compute_frequency_ranking(train_draws, training_window)
            pool = apply_temperature_to_selection(
                ranked, temperature, pool_size, band_dist
            )
        else:
            pool, _ = generate_dynamic_pool(
                train_draws, training_window, pool_size, band_dist
            )

        # Generate tickets via wheeling
        tickets, errors, _ = wheeling_reduction(pool, n_tickets, ticket_size)

        # Count aciertos for each ticket
        test_numbers = set(test_draw.numbers)
        best_aciertos = max(
            (len(set(t) & test_numbers) for t in tickets), default=0
        )

        # Hypergeometric baseline
        hyper_expected = 0.0
        if tickets:
            hyper_expected = compute_hypergeometric_expected_hits(
                tickets[0], 1
            )[0]

        # Monte Carlo baseline for remaining test periods
        remaining_test = len(draws) - (start + training_window + 1)
        mc_avg = 0.0
        if tickets and remaining_test > 0:
            mc_period_avgs, _ = run_monte_carlo_baseline(
                tickets[0], max(1, remaining_test), mc_simulations
            )
            mc_avg = mc_period_avgs[0] if mc_period_avgs else 0.0

        total_aciertos += best_aciertos
        total_hyper += hyper_expected
        total_mc += mc_avg

        cumulative_aciertos.append(total_aciertos)
        cumulative_hyper.append(total_hyper)
        cumulative_mc.append(total_mc)

        results.append({
            "test_draw_idx": start + training_window,
            "test_draw": test_draw,
            "train_window": (start, start + training_window),
            "best_aciertos": best_aciertos,
            "hyper_expected": hyper_expected,
            "mc_avg_aciertos": mc_avg,
            "tickets": tickets,
        })

    n_test_periods = len(results)
    hit_rate_user = total_aciertos / max(n_test_periods, 1)
    hit_rate_hyper = total_hyper / max(n_test_periods, 1)
    hit_rate_mc = total_mc / max(n_test_periods, 1)

    # Total cost: n_tickets volantes × n_test_periods × RD$75
    n_volantes = math.ceil(n_tickets / 3)  # 3 plays per volante
    total_cost = n_volantes * n_test_periods * COST_PER_VOLANTE

    return {
        "results": results,
        "cumulative_aciertos": cumulative_aciertos,
        "cumulative_hyper": cumulative_hyper,
        "cumulative_mc": cumulative_mc,
        "hit_rate_user": hit_rate_user,
        "hit_rate_hyper": hit_rate_hyper,
        "hit_rate_mc": hit_rate_mc,
        "n_test_periods": n_test_periods,
        "total_cost": total_cost,
        "temperature": temperature,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PREDICTIVE ANALYSIS ENGINE (Phase 7: BT-06)
# ═══════════════════════════════════════════════════════════════════════════════


def compute_cooccurrence_matrix(draws: List[Draw], window: int) -> pd.DataFrame:
    """Standalone co-occurrence matrix for all 80 numbers.

    For each pair (a, b) where a != b, count how many draws both appear in,
    normalized by total draws in window. Returns an 80x80 DataFrame.
    """
    subset = draws[-window:] if len(draws) >= window else draws
    n_draws = len(subset)

    # Count co-occurrences
    pair_counts: Dict[Tuple[int, int], int] = defaultdict(int)
    for draw in subset:
        nums = sorted(draw.numbers)
        for i, a in enumerate(nums):
            for b in nums[i + 1:]:
                pair_counts[(a, b)] += 1
                pair_counts[(b, a)] += 1

    # Normalize
    all_numbers = list(range(1, 81))
    data = np.zeros((80, 80), dtype=np.float64)
    for a in all_numbers:
        for b in all_numbers:
            if a != b:
                data[a - 1][b - 1] = pair_counts.get((a, b), 0) / max(n_draws, 1)

    return pd.DataFrame(data, index=all_numbers, columns=all_numbers)


def compute_temporal_patterns(draws: List[Draw], window: int) -> Dict:
    """Analyze temporal patterns: day-of-week, band trends, cyclical behavior."""
    subset = draws[-window:] if len(draws) >= window else draws
    n_draws = len(subset)

    # --- Day-of-week frequencies ---
    day_of_week_freq: Dict[int, Dict[int, float]] = {}
    day_counts: Dict[int, int] = defaultdict(int)
    day_num_freq: Dict[int, Counter] = defaultdict(Counter)

    for draw in subset:
        try:
            dt = datetime.fromisoformat(draw.date_iso)
            dow = dt.weekday()  # 0=Monday..6=Sunday
        except (ValueError, TypeError):
            continue
        day_counts[dow] += 1
        for n in draw.numbers:
            day_num_freq[dow][n] += 1

    for dow in range(7):
        total = max(day_counts.get(dow, 1), 1)
        day_of_week_freq[dow] = {
            n: cnt / total for n, cnt in day_num_freq[dow].items()
        }

    # --- Band trends (rolling averages at 10, 20, 30) ---
    band_trends: Dict[str, List[float]] = {"Baja": [], "Media": [], "Alta": []}
    band_cyclical: Dict[str, bool] = {"Baja": False, "Media": False, "Alta": False}
    recent_band_shift: Dict[str, float] = {"Baja": 0.0, "Media": 0.0, "Alta": 0.0}

    def _count_bands(draws_slice: List[Draw]) -> Dict[str, int]:
        counts = {"Baja": 0, "Media": 0, "Alta": 0}
        total_nums = 0
        for d in draws_slice:
            for n in d.numbers:
                total_nums += 1
                if n in BAND_LOW:
                    counts["Baja"] += 1
                elif n in BAND_MID:
                    counts["Media"] += 1
                else:
                    counts["Alta"] += 1
        return {k: v / max(total_nums, 1) for k, v in counts.items()}

    for band_name in ["Baja", "Media", "Alta"]:
        for window_size in [10, 20, 30]:
            if n_draws >= window_size:
                freqs = _count_bands(subset[-window_size:])
                band_trends[band_name].append(freqs[band_name])
            else:
                freqs = _count_bands(subset)
                band_trends[band_name].append(freqs[band_name])

        # Cyclical detection: check if frequency oscillates
        if len(band_trends[band_name]) >= 2:
            vals = band_trends[band_name]
            # Simple oscillation: alternating above/below mean
            mean_val = sum(vals) / len(vals)
            signs = [v - mean_val for v in vals]
            alternations = sum(
                1 for i in range(1, len(signs))
                if signs[i] * signs[i - 1] < 0
            )
            if alternations >= len(signs) - 1 and len(signs) >= 3:
                band_cyclical[band_name] = True

        # Recent band shift: last 10 vs previous 10
        if n_draws >= 20:
            recent_freqs = _count_bands(subset[-10:])
            prev_freqs = _count_bands(subset[-20:-10])
            recent_band_shift[band_name] = recent_freqs[band_name] - prev_freqs[band_name]
        elif n_draws >= 10:
            recent_freqs = _count_bands(subset[-10:])
            prev_freqs = _count_bands(subset[:max(1, n_draws - 10)])
            recent_band_shift[band_name] = recent_freqs[band_name] - prev_freqs[band_name]

    return {
        "day_of_week_freq": day_of_week_freq,
        "band_trends": band_trends,
        "band_cyclical": band_cyclical,
        "recent_band_shift": recent_band_shift,
    }


def compute_predictive_scores(
    draws: List[Draw], window: int, temperature: float = 1.0,
) -> Dict:
    """Main predictive scoring engine combining 6 factors.

    Factors: frequency, gap, co-occurrence, recency, temporal, band_trend.
    Returns confidence scores 0-100 for each number.
    """
    subset = draws[-window:] if len(draws) >= window else draws
    n_draws = len(subset)

    # --- Factor a: Frequency ranking (normalized 0-1) ---
    freq_ranked = compute_frequency_ranking(draws, window)
    freq_dict: Dict[int, float] = {}
    max_freq_score = max((s for _, s, _ in freq_ranked), default=1)
    for num, score, _ in freq_ranked:
        freq_dict[num] = score / max(max_freq_score, 1e-8)

    # --- Factor b: Gap score ---
    gap_df = compute_gap_analysis(draws, window)
    optimal_gap = window / 20.0  # Expected average gap for 20 numbers in 80
    gap_scores: Dict[int, float] = {}
    for _, row in gap_df.iterrows():
        num = int(row["Numero"])
        gap = row["Gap"]
        gap_scores[num] = max(0.0, 1.0 - abs(gap - optimal_gap) / max(window, 1))

    # --- Factor c: Co-occurrence (average with top-20 numbers) ---
    cooc_df = compute_cooccurrence_matrix(draws, window)
    top20_nums = [n for n, _, _ in freq_ranked[:20]]
    cooc_scores: Dict[int, float] = {}
    for num in range(1, 81):
        cooc_vals = [cooc_df.loc[num, t] for t in top20_nums if t != num]
        cooc_scores[num] = float(np.mean(cooc_vals)) if cooc_vals else 0.0

    # Normalize co-occurrence
    max_cooc = max(cooc_scores.values(), default=1)
    for num in cooc_scores:
        cooc_scores[num] /= max(max_cooc, 1e-8)

    # --- Factor d: Temperature-weighted recency ---
    decay = 1.0 / max(temperature, 1e-8)
    recency_scores: Dict[int, float] = {}
    for num in range(1, 81):
        weight_sum = 0.0
        for idx, draw in enumerate(subset):
            if num in draw.numbers:
                weight_sum += math.exp(-decay * (n_draws - 1 - idx))
        recency_scores[num] = weight_sum

    max_recency = max(recency_scores.values(), default=1)
    for num in recency_scores:
        recency_scores[num] /= max(max_recency, 1e-8)

    # --- Factor e: Temporal pattern (day-of-week boost) ---
    temporal = compute_temporal_patterns(draws, window)
    today_dow = datetime.now().weekday()
    temporal_scores: Dict[int, float] = {}
    day_freqs = temporal["day_of_week_freq"].get(today_dow, {})
    max_temporal = max(day_freqs.values(), default=1) if day_freqs else 1
    for num in range(1, 81):
        temporal_scores[num] = day_freqs.get(num, 0) / max(max_temporal, 1e-8)

    # --- Factor f: Band trend boost ---
    band_scores: Dict[int, float] = {}
    shift = temporal["recent_band_shift"]
    for num in range(1, 81):
        if num in BAND_LOW:
            band_scores[num] = shift.get("Baja", 0.0)
        elif num in BAND_MID:
            band_scores[num] = shift.get("Media", 0.0)
        else:
            band_scores[num] = shift.get("Alta", 0.0)

    # Normalize band scores to 0-1
    band_vals = list(band_scores.values())
    if band_vals:
        b_min, b_max = min(band_vals), max(band_vals)
        b_range = b_max - b_min if b_max != b_min else 1.0
        for num in band_scores:
            band_scores[num] = (band_scores[num] - b_min) / b_range

    # --- Combined score ---
    weights = {
        "frequency": 0.25,
        "gap": 0.15,
        "cooccurrence": 0.20,
        "recency": 0.15,
        "temporal": 0.10,
        "band_trend": 0.15,
    }

    combined: Dict[int, float] = {}
    for num in range(1, 81):
        combined[num] = (
            weights["frequency"] * freq_dict.get(num, 0)
            + weights["gap"] * gap_scores.get(num, 0)
            + weights["cooccurrence"] * cooc_scores.get(num, 0)
            + weights["recency"] * recency_scores.get(num, 0)
            + weights["temporal"] * temporal_scores.get(num, 0)
            + weights["band_trend"] * band_scores.get(num, 0)
        )

    # Normalize to 0-100
    max_combined = max(combined.values(), default=1)
    min_combined = min(combined.values(), default=0)
    c_range = max_combined - min_combined if max_combined != min_combined else 1.0

    number_scores = []
    for num in range(1, 81):
        normalized = (combined[num] - min_combined) / c_range * 100
        number_scores.append({
            "number": num,
            "score": round(normalized, 1),
            "factors": {
                "frequency": round(freq_dict.get(num, 0), 4),
                "gap": round(gap_scores.get(num, 0), 4),
                "cooccurrence": round(cooc_scores.get(num, 0), 4),
                "recency": round(recency_scores.get(num, 0), 4),
                "temporal": round(temporal_scores.get(num, 0), 4),
                "band_trend": round(band_scores.get(num, 0), 4),
            },
        })

    number_scores.sort(key=lambda x: x["score"], reverse=True)

    # Top co-occurring pairs
    top_pairs: List[Tuple[int, int, float]] = []
    seen = set()
    for a in range(1, 81):
        for b in range(a + 1, 81):
            val = cooc_df.loc[a, b]
            if val > 0:
                top_pairs.append((a, b, float(val)))
    top_pairs.sort(key=lambda x: x[2], reverse=True)

    return {
        "number_scores": number_scores,
        "temporal_patterns": temporal,
        "cooccurrence_top_pairs": top_pairs[:20],
    }


def suggest_band_distribution(
    draws: List[Draw], window: int, predictive_scores: Dict,
) -> Dict:
    """Suggest optimal band distribution based on historical patterns and trends."""
    subset = draws[-window:] if len(draws) >= window else draws

    # Historical band frequency over window
    band_counts = {"Baja": 0, "Media": 0, "Alta": 0}
    total_nums = 0
    for draw in subset:
        for n in draw.numbers:
            total_nums += 1
            if n in BAND_LOW:
                band_counts["Baja"] += 1
            elif n in BAND_MID:
                band_counts["Media"] += 1
            else:
                band_counts["Alta"] += 1

    band_freq = {k: v / max(total_nums, 1) for k, v in band_counts.items()}

    # Expected proportional (26/80, 28/80, 26/80)
    expected = {"Baja": 26 / 80, "Media": 28 / 80, "Alta": 26 / 80}

    # Trend analysis
    temporal = predictive_scores.get("temporal_patterns", {})
    shift = temporal.get("recent_band_shift", {})
    cyclical = temporal.get("band_cyclical", {})

    # Score each band
    band_analysis: Dict[str, Dict] = {}
    for band in ["Baja", "Media", "Alta"]:
        freq = band_freq.get(band, 0)
        trend_val = shift.get(band, 0.0)
        is_hot = freq > expected[band]
        is_cold = freq < expected[band]

        if trend_val > 0.01:
            trend = "up"
        elif trend_val < -0.01:
            trend = "down"
        else:
            trend = "stable"

        if is_hot:
            hot_cold = "hot"
        elif is_cold:
            hot_cold = "cold"
        else:
            hot_cold = "neutral"

        band_analysis[band] = {
            "frequency": freq,
            "trend": trend,
            "hot_cold": hot_cold,
            "shift": trend_val,
            "cyclical": cyclical.get(band, False),
        }

    # Determine suggested distribution (10 numbers total)
    # Start from expected proportional and adjust
    base = {"Baja": 3, "Media": 4, "Alta": 3}  # 3-4-3 base

    for band in ["Baja", "Media", "Alta"]:
        info = band_analysis[band]
        if info["trend"] == "up" and info["hot_cold"] in ("hot", "neutral"):
            base[band] += 1
        elif info["trend"] == "down" and info["hot_cold"] == "cold":
            base[band] -= 1

    # Ensure all >= 0 and sum = 10
    for band in base:
        base[band] = max(0, base[band])

    total = sum(base.values())
    if total != 10:
        # Adjust the band with the highest frequency
        diff = 10 - total
        sorted_bands = sorted(base.keys(), key=lambda b: band_freq.get(b, 0), reverse=True)
        idx = 0
        while sum(base.values()) != 10 and idx < 100:
            band = sorted_bands[idx % 3]
            if diff > 0:
                base[band] += 1
                diff -= 1
            elif diff < 0 and base[band] > 0:
                base[band] -= 1
                diff += 1
            idx += 1

    suggested = (base["Baja"], base["Media"], base["Alta"])

    # Confidence: based on how consistent trends are
    trend_consistency = sum(
        1 for b in ["Baja", "Media", "Alta"]
        if band_analysis[b]["trend"] != "stable"
    )
    confidence = 50 + trend_consistency * 15  # 50-95 range
    confidence = min(confidence, 95)

    # Reasoning
    parts = []
    for band in ["Baja", "Media", "Alta"]:
        info = band_analysis[band]
        direction = "↑" if info["trend"] == "up" else "↓" if info["trend"] == "down" else "→"
        pct = info["shift"] * 100
        parts.append(f"{band} {direction} ({pct:+.1f}%)")
    reasoning = ", ".join(parts)

    # Alternative distributions
    alternatives = []
    # Proportional distribution
    alt_prop = (3, 4, 3)
    alternatives.append({
        "dist": alt_prop,
        "confidence": 60,
        "reason": "Distribucion proporcional basica (3-4-3)",
    })
    # All-hot distribution
    hot_bands = [b for b, info in band_analysis.items() if info["hot_cold"] == "hot"]
    if hot_bands:
        alt_hot = list(alt_prop)
        for band in hot_bands:
            idx = ["Baja", "Media", "Alta"].index(band)
            alt_hot[idx] += 1
            other_idx = (idx + 1) % 3
            if alt_hot[other_idx] > 1:
                alt_hot[other_idx] -= 1
        total_alt = sum(alt_hot)
        if total_alt == 10:
            alternatives.append({
                "dist": tuple(alt_hot),
                "confidence": 70,
                "reason": f"Priorizar franjas calientes: {', '.join(hot_bands)}",
            })

    return {
        "suggested_distribution": suggested,
        "confidence": float(confidence),
        "reasoning": reasoning,
        "alternative_distributions": alternatives,
        "band_analysis": band_analysis,
    }


def recommend_tickets(
    draws: List[Draw],
    predictive_scores: Dict,
    band_suggestion: Dict,
    config: Dict,
) -> Dict:
    """Generate recommended ticket compositions based on predictive scores."""
    suggested_dist = band_suggestion["suggested_distribution"]
    low_n, mid_n, high_n = suggested_dist
    n_tickets = config.get("n_tickets", 18)

    # Split numbers by band with scores
    scored = predictive_scores["number_scores"]
    low_nums = [(s["number"], s["score"]) for s in scored if s["number"] in BAND_LOW]
    mid_nums = [(s["number"], s["score"]) for s in scored if s["number"] in BAND_MID]
    high_nums = [(s["number"], s["score"]) for s in scored if s["number"] in BAND_HIGH]

    recommended_tickets: List[Dict] = []
    pool_used: List[int] = []
    total_score = 0.0

    # Generate min(n_tickets, possible combinations) tickets
    max_tickets = min(n_tickets, 10)

    for i in range(max_tickets):
        # Select top numbers from each band (with slight rotation for variety)
        offset = i % 3
        ticket_low = [n for n, _ in low_nums[offset:offset + low_n]]
        ticket_mid = [n for n, _ in mid_nums[offset:offset + mid_n]]
        ticket_high = [n for n, _ in high_nums[offset:offset + high_n]]

        # Fill if any band is short
        all_ticket = ticket_low + ticket_mid + ticket_high
        if len(all_ticket) < 10:
            remaining = [s["number"] for s in scored if s["number"] not in all_ticket]
            all_ticket.extend(remaining[: 10 - len(all_ticket)])

        all_ticket = sorted(all_ticket[:10])

        if len(all_ticket) < 10:
            continue

        # Compute average score
        ticket_scores = [s["score"] for s in scored if s["number"] in all_ticket]
        avg_score = sum(ticket_scores) / len(ticket_scores) if ticket_scores else 0.0

        # Band counts
        b_count = sum(1 for n in all_ticket if n in BAND_LOW)
        m_count = sum(1 for n in all_ticket if n in BAND_MID)
        a_count = sum(1 for n in all_ticket if n in BAND_HIGH)

        # Reasoning
        high_score_nums = [n for n in all_ticket if any(
            s["number"] == n and s["score"] > 60 for s in scored
        )]
        reasoning_parts = []
        if high_score_nums:
            reasoning_parts.append(
                f"Numeros de alta confianza: {', '.join(f'{n:02d}' for n in high_score_nums[:3])}"
            )
        reasoning_parts.append(
            f"Franja: {b_count} Baja, {m_count} Media, {a_count} Alta "
            f"({band_suggestion['confidence']:.0f}% confianza)"
        )
        reasoning = ". ".join(reasoning_parts)

        recommended_tickets.append({
            "numbers": tuple(all_ticket),
            "reasoning": reasoning,
            "score": round(avg_score, 1),
            "band_dist": (b_count, m_count, a_count),
        })

        total_score += avg_score
        pool_used.extend(all_ticket)

    pool_used = sorted(set(pool_used))
    avg_total = total_score / max(len(recommended_tickets), 1)

    return {
        "recommended_tickets": recommended_tickets,
        "pool_used": pool_used,
        "total_score": round(avg_total, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar(n_draws: int) -> Dict:
    """Render sidebar controls and return configuration dict.

    Per D-10: No preset selector — always Personalizada.
    Per D-08: Band values auto-recalculate when pool_size changes.
    Per D-09: Block generation if Baja+Media+Alta != pool_size.
    Per D-11: Band metrics displayed with colored text.
    """
    st.sidebar.header(":material/tune: Configuracion")

    # --- Window slider (CTRL-01) ---
    max_window = min(100, n_draws)
    window = st.sidebar.slider(
        "Ventana de sorteos (retroactivos)",
        min_value=10,
        max_value=max_window,
        value=max_window,
        help="Maximo 100 sorteos retroactivos desde el ultimo sorteo cargado.",
    )

    st.sidebar.divider()

    # --- Pool size (CTRL-02) ---
    pool_size = st.sidebar.slider(
        "Tamano del Pool Dinamico",
        min_value=15,
        max_value=30,
        value=20,
        help="Cantidad de numeros en el pool generado automaticamente.",
        key="tamano_del_pool_dinamico",
        on_change=_recalc_bands_on_pool_change,
    )

    # --- Ticket quantity (CTRL-03) ---
    n_tickets = st.sidebar.slider(
        "Cantidad de Boletos (Wheeling)",
        min_value=6,
        max_value=30,
        value=18,
        help="Numero de combinaciones a generar via reduccion combinatoria.",
    )

    st.sidebar.divider()

    # --- Band Distribution (CTRL-04, D-10: forced Personalizada) ---
    st.sidebar.subheader("Distribucion por Franja")
    st.sidebar.caption("Baja: 01-26 | Media: 27-54 | Alta: 55-80")

    # Default proportional values for first load (proportional to pool_size)
    default_baja = max(1, round(pool_size * 26 / 80))
    default_media = max(1, round(pool_size * 28 / 80))
    default_alta = pool_size - default_baja - default_media
    if default_alta < 0:
        default_alta = 0
        default_media = pool_size - default_baja

    # Three number inputs per D-10 (forced Personalizada — no preset selector)
    # Using key param so Streamlit manages session state automatically
    baja = st.number_input(
        "Baja",
        min_value=0,
        max_value=pool_size,
        value=st.session_state.get("_band_baja", default_baja),
        key="_band_baja",
        help="Numeros en rango 01-26",
    )
    media = st.number_input(
        "Media",
        min_value=0,
        max_value=pool_size,
        value=st.session_state.get("_band_media", default_media),
        key="_band_media",
        help="Numeros en rango 27-54",
    )
    alta = st.number_input(
        "Alta",
        min_value=0,
        max_value=pool_size,
        value=st.session_state.get("_band_alta", default_alta),
        key="_band_alta",
        help="Numeros en rango 55-80",
    )

    total = baja + media + alta

    # D-11: Colored band metrics
    st.sidebar.divider()
    col_b, col_m, col_a = st.sidebar.columns(3)
    with col_b:
        st.metric(label="Baja", value=baja, delta=":blue[Baja]")
    with col_m:
        st.metric(label="Media", value=media, delta=":orange[Media]")
    with col_a:
        st.metric(label="Alta", value=alta, delta=":red[Alta]")

    # D-09: Sum validation — BLOCK if mismatch
    band_dist = (baja, media, alta)
    band_valid = True
    if total != pool_size:
        st.sidebar.error(
            f":material/error: La suma ({total}) no coincide con el pool ({pool_size}). "
            f"Ajuste los valores."
        )
        band_valid = False

    # ═══════════════════════════════════════════════════════════════════════════
    # PER-TICKET BAND DISTRIBUTION (Phase 5: BAND-01, BAND-04)
    # ═══════════════════════════════════════════════════════════════════════════
    st.sidebar.divider()
    st.sidebar.subheader("Distribucion por Boleto")

    # Preset selector (5 presets + Custom)
    preset_options = list(TICKET_BAND_PRESETS.keys()) + ["Custom"]
    selected_preset = st.sidebar.selectbox(
        "Esquema de distribucion",
        preset_options,
        key="_ticket_band_preset",
        help="Selecciona un preset o Custom para definir manualmente",
    )

    if selected_preset == "Custom":
        custom_b = st.sidebar.number_input(
            "Baja (por boleto)", min_value=0, max_value=10, value=4, key="_custom_tb"
        )
        custom_m = st.sidebar.number_input(
            "Media (por boleto)", min_value=0, max_value=10, value=3, key="_custom_tm"
        )
        custom_a = st.sidebar.number_input(
            "Alta (por boleto)", min_value=0, max_value=10, value=3, key="_custom_ta"
        )
        ticket_band_dist = (custom_b, custom_m, custom_a)
        ticket_band_sum = custom_b + custom_m + custom_a
        if ticket_band_sum != 10:
            st.sidebar.error(
                f":material/error: La suma ({ticket_band_sum}) debe ser 10 (tamano del boleto)"
            )
            ticket_band_valid = False
        else:
            ticket_band_valid = True
    else:
        ticket_band_dist = TICKET_BAND_PRESETS[selected_preset]
        ticket_band_valid = True

    # Uniform vs Variable toggle
    distribution_mode = st.sidebar.radio(
        "Modo de distribucion",
        ["Uniforme", "Variable"],
        key="_distribution_mode",
        help="Uniforme: todos los boletos con la misma distribucion. Variable: el wheeling puede variar por boleto",
    )
    uniform_mode = distribution_mode == "Uniforme"

    # Phase 6: Temperature control
    st.sidebar.divider()
    st.sidebar.subheader("Control de Temperatura")
    temperature = st.sidebar.slider(
        "Temperatura T",
        min_value=0.05,
        max_value=2.0,
        value=1.0,
        step=0.05,
        help="T baja = numeros frecuentes (determinista). T alta = distribucion uniforme (aleatorio). T=2.0 ≈ random.",
        key="temperature_t",
    )

    return {
        "window": window,
        "pool_size": pool_size,
        "n_tickets": n_tickets,
        "band_dist": band_dist,
        "band_valid": band_valid,
        "ticket_band_dist": ticket_band_dist,
        "ticket_band_valid": ticket_band_valid,
        "uniform_mode": uniform_mode,
        "selected_preset": selected_preset,
        "temperature": temperature,
    }


def _recalc_bands_on_pool_change() -> None:
    """D-08: Recalculate band values proportionally when pool_size changes.

    Called via on_change callback on the pool size slider.
    Reads new pool value from st.session_state (not callback args).
    """
    new_pool = st.session_state.get("tamano_del_pool_dinamico", 20)
    prev_pool = st.session_state.get("_prev_pool_size", new_pool)
    if new_pool == prev_pool:
        return
    st.session_state["_prev_pool_size"] = new_pool

    old_baja = st.session_state.get("_band_baja", 0)
    old_media = st.session_state.get("_band_media", 0)
    old_alta = st.session_state.get("_band_alta", 0)
    old_total = old_baja + old_media + old_alta

    if old_total > 0:
        new_baja = max(0, round(new_pool * old_baja / old_total))
        new_media = max(0, round(new_pool * old_media / old_total))
        new_alta = new_pool - new_baja - new_media
        if new_alta < 0:
            new_alta = 0
            new_media = new_pool - new_baja
        st.session_state["_band_baja"] = new_baja
        st.session_state["_band_media"] = new_media
        st.session_state["_band_alta"] = new_alta


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: MATRICES INTERMEDIAS
# ═══════════════════════════════════════════════════════════════════════════════

def render_tab_matrices(draws: List[Draw], config: Dict):
    """Render the intermediate matrices tab."""
    st.header("Matrices Intermedias")

    window = config["window"]

    # 1. 100x20 Intermediate Matrix with conditional formatting
    st.subheader(f"Matriz Intermedia {window} x 20")
    st.caption(
        f"Cada fila es un sorteo ordenado, columnas P1-P20 son las posiciones "
        f"(menor a mayor). Mostrando ultimos {window} sorteos. "
        f"Celdas con numeros resaltadas en azul, ceros en gris."
    )

    df_inter = compute_intermediate_matrix(draws, window)

    def _style_intermediate_matrix(val):
        """Highlight cells with presence (non-zero), neutral for zeros."""
        if val == 0 or val == 0.0:
            return "background-color: #f0f0f0; color: #999999"
        return "background-color: #e3f2fd; color: #1565c0; font-weight: bold"

    try:
        styled = df_inter.style.map(_style_intermediate_matrix)
    except AttributeError:
        styled = df_inter.style.applymap(_style_intermediate_matrix)
    st.dataframe(styled, width="stretch", height=400, use_container_width=True)

    st.divider()

    # 2. 10x10 Positional Frequency Matrix with totals
    st.subheader("Matriz 10 x 10 de Frecuencias Posicionales")
    st.caption(
        "Agrupada por pares de carriles adyacentes: "
        "C1=(B1,B2), C2=(B3,B4), ..., C10=(B19,B20). "
        "Cada celda cuenta cuantos numeros de cada franja aparecen en esas posiciones."
    )

    df_freq = compute_positional_frequency_matrix(draws, window)
    st.dataframe(df_freq, width="stretch")

    # Add totals row
    df_freq_with_totals = df_freq.copy()
    df_freq_with_totals.loc["Total"] = df_freq_with_totals.sum()
    st.subheader("Tabla de Frecuencias con Totales")
    st.dataframe(df_freq_with_totals, width="stretch")

    # Heatmap visualization
    try:
        import plotly.express as px

        fig = px.imshow(
            df_freq.values,
            labels=dict(x="Column Group", y="Franja", color="Frecuencia"),
            x=df_freq.columns.tolist(),
            y=df_freq.index.tolist(),
            color_continuous_scale="YlOrRd",
            title="Frecuencia Posicional por Franja y Carril",
        )
        st.plotly_chart(fig, width="stretch")
    except ImportError:
        st.info("Instala plotly para visualizaciones: `pip install plotly`")

    # Numbers by zone heatmap (informative)
    st.subheader("Numeros por Posicion y Franja")
    st.caption(
        "Lista de numeros que aparecen en cada zona (franja × grupo de carril). "
        "Ayuda a identificar visualmente las zonas mas calientes."
    )

    subset = draws[-window:] if len(draws) >= window else draws
    zone_numbers: Dict[str, Dict[str, List[int]]] = {
        "Baja(01-26)": {f"C{i+1}": [] for i in range(10)},
        "Media(27-54)": {f"C{i+1}": [] for i in range(10)},
        "Alta(55-80)": {f"C{i+1}": [] for i in range(10)},
    }

    for draw in subset:
        nums = draw.numbers
        for col_group in range(10):
            pos_a = col_group * 2
            pos_b = col_group * 2 + 1
            for pos in [pos_a, pos_b]:
                if pos < len(nums):
                    n = nums[pos]
                    if n in BAND_LOW:
                        zone_numbers["Baja(01-26)"][f"C{col_group+1}"].append(n)
                    elif n in BAND_MID:
                        zone_numbers["Media(27-54)"][f"C{col_group+1}"].append(n)
                    else:
                        zone_numbers["Alta(55-80)"][f"C{col_group+1}"].append(n)

    # Create display DataFrame with unique sorted numbers per cell
    zone_display: Dict[str, Dict[str, str]] = {}
    zone_counts: Dict[str, Dict[str, int]] = {}
    for band, cols in zone_numbers.items():
        zone_display[band] = {}
        zone_counts[band] = {}
        for col, nums in cols.items():
            unique_sorted = sorted(set(nums))
            zone_display[band][col] = ", ".join(str(n) for n in unique_sorted) if unique_sorted else "-"
            zone_counts[band][col] = len(unique_sorted)

    df_zone = pd.DataFrame(zone_display)
    df_counts = pd.DataFrame(zone_counts)

    # Style with color intensity based on count
    def _style_zone(val: str, band: str, col: str) -> str:
        count = zone_counts.get(band, {}).get(col, 0)
        if count == 0:
            return "background-color: #f5f5f5; color: #999"
        intensity = min(count / 15.0, 1.0)
        r = int(255 - intensity * 30)
        g = int(255 - intensity * 80)
        b = int(255 - intensity * 20)
        return f"background-color: rgb({r},{g},{b}); color: #333; font-size: 0.85em"

    styled_zones = pd.DataFrame(index=df_zone.index, columns=df_zone.columns)
    for band in df_zone.index:
        for col in df_zone.columns:
            styled_zones.loc[band, col] = _style_zone(df_zone.loc[band, col], band, col)

    st.dataframe(df_zone, width="stretch")

    # Scatter plot with marginal histograms
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        scatter_data: List[Dict] = []
        for draw in subset:
            nums = draw.numbers
            for col_group in range(10):
                pos_a = col_group * 2
                pos_b = col_group * 2 + 1
                for pos in [pos_a, pos_b]:
                    if pos < len(nums):
                        n = nums[pos]
                        if n in BAND_LOW:
                            band = "Baja"
                        elif n in BAND_MID:
                            band = "Media"
                        else:
                            band = "Alta"
                        scatter_data.append({
                            "Numero": n,
                            "Grupo": f"C{col_group+1}",
                            "Franja": band,
                        })

        df_scatter = pd.DataFrame(scatter_data)

        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.85, 0.15],
            row_heights=[0.85, 0.15],
            horizontal_spacing=0.02,
            vertical_spacing=0.02,
            specs=[
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "bar"}, None],
            ],
        )

        color_map = {"Baja": "#1565c0", "Media": "#f9a825", "Alta": "#c62828"}

        for band in ["Baja", "Media", "Alta"]:
            df_b = df_scatter[df_scatter["Franja"] == band]
            fig.add_trace(
                go.Scatter(
                    x=df_b["Grupo"],
                    y=df_b["Numero"],
                    mode="markers",
                    name=band,
                    marker=dict(color=color_map[band], opacity=0.5, size=4),
                    showlegend=True,
                ),
                row=1, col=1,
            )

        # Marginal histogram: numbers by band (right side)
        for band in ["Baja", "Media", "Alta"]:
            df_b = df_scatter[df_scatter["Franja"] == band]
            fig.add_trace(
                go.Histogram(
                    y=df_b["Numero"],
                    orientation="h",
                    marker_color=color_map[band],
                    showlegend=False,
                    nbinsy=20,
                ),
                row=1, col=2,
            )

        # Marginal histogram: groups by band (bottom)
        for band in ["Baja", "Media", "Alta"]:
            df_b = df_scatter[df_scatter["Franja"] == band]
            fig.add_trace(
                go.Histogram(
                    x=df_b["Grupo"],
                    marker_color=color_map[band],
                    showlegend=False,
                ),
                row=2, col=1,
            )

        fig.update_xaxes(title_text="Grupo de Carril", row=2, col=1)
        fig.update_yaxes(title_text="Numero", row=1, col=1)
        fig.update_layout(
            height=600,
            title_text="Distribucion de Numeros por Posicion y Franja",
            legend_title_text="Franja",
        )

        st.plotly_chart(fig, width="stretch")
    except ImportError:
        st.info("Instala plotly para visualizaciones: `pip install plotly`")

    st.divider()

    # 3. Gap Analysis (D-11)
    st.subheader("Analisis de Brechas (Gap Analysis)")
    st.caption(
        f"Cuantos sorteos han pasado desde la ultima aparicion de cada numero. "
        f"Numeros con gap alto = frios (no aparecen recientemente). "
        f"Ventana: {window} sorteos."
    )

    df_gap = compute_gap_analysis(draws, window)

    # Show top 20 coldest numbers
    st.markdown("**Top 20 Numeros mas Frios:**")
    st.dataframe(df_gap.head(20), width="stretch")

    # Bar chart for top 20 coldest numbers
    df_top20 = df_gap.head(20).copy()
    df_top20["Numero"] = df_top20["Numero"].astype(str)
    st.bar_chart(df_top20.set_index("Numero")["Gap"])

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_gap = df_gap["Gap"].mean()
        st.metric("Gap Promedio", f"{avg_gap:.1f}")
    with col2:
        max_gap = df_gap["Gap"].max()
        st.metric("Gap Maximo", int(max_gap))
    with col3:
        cold_threshold = window // 2
        cold_count = len(df_gap[df_gap["Gap"] > cold_threshold])
        st.metric("Numeros Frios", cold_count, delta=f"gap > {cold_threshold}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: POOL DINAMICO
# ═══════════════════════════════════════════════════════════════════════════════

def render_tab_pool(draws: List[Draw], config: Dict):
    """Render the dynamic pool tab."""
    st.header("Pool Dinamico")

    window = config["window"]
    pool_size = config["pool_size"]
    band_dist = config["band_dist"]

    # Generate pool
    pool, band_counts = generate_dynamic_pool(draws, window, pool_size, band_dist)

    # Part A: Pool number display with band color coding (D-08)
    st.subheader(f"Pool Dinamico — {len(pool)} Numeros")
    st.caption("Numeros del pool con indicador de franja: Baja=azul, Media=amarillo, Alta=rojo.")

    cols = st.columns(10)
    for i, num in enumerate(pool):
        col = cols[i % 10]
        with col:
            if num in BAND_LOW:
                st.metric(
                    label=f"{num:02d}",
                    value=num,
                    delta="Baja",
                    delta_color="inverse",
                )
            elif num in BAND_MID:
                st.metric(
                    label=f"{num:02d}",
                    value=num,
                    delta="Media",
                    delta_color="off",
                )
            else:
                st.metric(
                    label=f"{num:02d}",
                    value=num,
                    delta="Alta",
                    delta_color="normal",
                )

    st.divider()

    # Part B: Band metrics matching sidebar distribution (D-07)
    st.subheader("Metricas por Franja")
    st.caption(
        f"Distribucion configurada: Baja={band_dist[0]}, Media={band_dist[1]}, "
        f"Alta={band_dist[2]} (total={sum(band_dist)})"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        actual_baja = band_counts.get("Baja (01-26)", 0)
        delta_baja = actual_baja - band_dist[0]
        st.metric(
            "Baja (01-26)",
            actual_baja,
            delta=f"{delta_baja:+d} vs configurado" if delta_baja != 0 else "Correcto",
            delta_color="inverse" if delta_baja < 0 else ("normal" if delta_baja > 0 else "off"),
        )
    with col2:
        actual_media = band_counts.get("Media (27-54)", 0)
        delta_media = actual_media - band_dist[1]
        st.metric(
            "Media (27-54)",
            actual_media,
            delta=f"{delta_media:+d} vs configurado" if delta_media != 0 else "Correcto",
            delta_color="inverse" if delta_media < 0 else ("normal" if delta_media > 0 else "off"),
        )
    with col3:
        actual_alta = band_counts.get("Alta (55-80)", 0)
        delta_alta = actual_alta - band_dist[2]
        st.metric(
            "Alta (55-80)",
            actual_alta,
            delta=f"{delta_alta:+d} vs configurado" if delta_alta != 0 else "Correcto",
            delta_color="inverse" if delta_alta < 0 else ("normal" if delta_alta > 0 else "off"),
        )

    # Distribution bar
    dist_df = pd.DataFrame(
        list(band_counts.items()), columns=["Franja", "Cantidad"]
    )
    st.bar_chart(dist_df.set_index("Franja"))

    st.divider()

    # Part C: Full 80-number ranking table (D-09, D-10)
    st.subheader("Ranking Completo de Numeros (80 numeros)")
    st.caption(
        "Score = frecuencia_normalizada + 0.3 * co-ocurrencia_normalizada. "
        "Numeros en el pool estan marcados con asterisco."
    )

    ranked = compute_frequency_ranking(draws, window)
    pool_set = set(pool)

    ranked_rows = []
    for rank_idx, (num, score, freq) in enumerate(ranked, 1):
        in_pool = num in pool_set
        ranked_rows.append({
            "Rank": rank_idx,
            "Numero": f"{num:02d}{'*' if in_pool else ''}",
            "Score": round(score, 4),
            "Frecuencia": freq,
            "En_Pool": "Si" if in_pool else "No",
        })

    df_ranked = pd.DataFrame(ranked_rows)
    df_ranked = df_ranked.set_index("Rank")
    st.dataframe(df_ranked, width="stretch")

    pool_in_ranking = len([r for r in ranked_rows if r["En_Pool"] == "Si"])
    st.caption(f"Numeros en pool: {pool_in_ranking} de {len(pool)} seleccionados aparecen en el top {len(pool)} del ranking.")

    st.divider()

    # Part D: Gap analysis context for pool numbers
    st.subheader("Contexto de Brechas (Gap Analysis)")
    st.caption("Cuantos sorteos desde la ultima aparicion de cada numero en el pool.")

    gap_df = compute_gap_analysis(draws, window)
    gap_pool = gap_df[gap_df["Numero"].isin(pool_set)].copy()
    gap_pool = gap_pool.sort_values("Gap", ascending=False).reset_index(drop=True)
    gap_pool.index = range(1, len(gap_pool) + 1)
    gap_pool.index.name = "Rank"

    st.dataframe(gap_pool, width="stretch")

    cold_threshold = window // 3
    cold_in_pool = len(gap_pool[gap_pool["Gap"] > cold_threshold])
    hot_in_pool = len(gap_pool[gap_pool["Gap"] <= cold_threshold])

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Numeros Frios en Pool",
            cold_in_pool,
            delta=f"gap > {cold_threshold} sorteos",
            delta_color="normal",
        )
    with col2:
        st.metric(
            "Numeros Calientes en Pool",
            hot_in_pool,
            delta=f"gap <= {cold_threshold} sorteos",
            delta_color="inverse",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: VOLANTES & WHEELING
# ═══════════════════════════════════════════════════════════════════════════════

def render_tab_tickets(draws: List[Draw], config: Dict):
    """Render the volantes & wheeling tab."""
    st.header("Volantes & Reduccion Combinatoria")

    window = config["window"]
    pool_size = config["pool_size"]
    n_tickets = config["n_tickets"]
    band_dist = config["band_dist"]

    # Generate pool
    pool, band_counts = generate_dynamic_pool(draws, window, pool_size, band_dist)

    st.info(f"Pool base: {pool}")

    # Phase 5: Validate pool can satisfy per-ticket band distribution
    ticket_band_dist = config.get("ticket_band_dist")
    ticket_band_valid = config.get("ticket_band_valid", True)
    uniform_mode = config.get("uniform_mode", True)

    if ticket_band_valid and ticket_band_dist is not None:
        pool_baja = sum(1 for n in pool if n in BAND_LOW)
        pool_media = sum(1 for n in pool if n in BAND_MID)
        pool_alta = sum(1 for n in pool if n in BAND_HIGH)
        tb, tm, ta = ticket_band_dist
        pool_errors = []
        preset_name = config.get("selected_preset", "Custom")
        if pool_baja < tb:
            pool_errors.append(
                f"Pool no tiene suficientes numeros Baja ({pool_baja}) "
                f"para esquema {preset_name} (necesita {tb})"
            )
        if pool_media < tm:
            pool_errors.append(
                f"Pool no tiene suficientes numeros Media ({pool_media}) "
                f"para esquema {preset_name} (necesita {tm})"
            )
        if pool_alta < ta:
            pool_errors.append(
                f"Pool no tiene suficientes numeros Alta ({pool_alta}) "
                f"para esquema {preset_name} (necesita {ta})"
            )
        if pool_errors:
            for e in pool_errors:
                st.sidebar.error(f":material/error: {e}")
            ticket_band_valid = False

    # Block generation if ticket_band_valid is False
    if not ticket_band_valid:
        st.warning("Ajuste la distribucion por boleto antes de generar.")
        return

    # Execute wheeling — store in session_state
    if st.button("Generar Boletos", type="primary", key="gen_tickets"):
        with st.spinner("Ejecutando reduccion combinatoria determinista..."):
            tickets, wheel_errors, ticket_bands = wheeling_reduction(
                pool, n_tickets, ticket_size=10,
                ticket_band_dist=ticket_band_dist,
                uniform=uniform_mode,
            )

        if wheel_errors:
            for err in wheel_errors:
                st.warning(err)

        if not tickets:
            st.error("No se pudieron generar boletos. Verifica el pool y parametros.")
            return

        volantes = group_into_volantes(tickets)
        st.session_state.generated_tickets = tickets
        st.session_state.generated_volantes = volantes
        st.session_state.generated_pool = pool
        st.session_state.generated_ticket_bands = ticket_bands
        st.rerun()

    # Display generated tickets (from session_state)
    tickets = st.session_state.get("generated_tickets", [])
    volantes = st.session_state.get("generated_volantes", [])
    saved_pool = st.session_state.get("generated_pool", [])
    ticket_bands_data = st.session_state.get("generated_ticket_bands", [])

    if not tickets:
        st.info("Haz clic en 'Generar Boletos' para comenzar.")
        return

    # Summary metrics
    st.subheader("Resumen")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Boletos generados", len(tickets))
    with col2:
        st.metric("Volantes", len(volantes))
    with col3:
        total_cost = len(volantes) * COST_PER_VOLANTE
        st.metric("Costo Total", f"RD${total_cost:,}")

    # Phase 5: Per-ticket band composition display
    if ticket_bands_data:
        st.subheader("Distribucion por Boleto")
        band_df_data = []
        for i, (ticket, bands) in enumerate(zip(tickets, ticket_bands_data)):
            b, m, a = bands
            band_df_data.append({
                "Boleto": i + 1,
                "Numeros": ", ".join(f"{n:02d}" for n in ticket),
                "Baja": b,
                "Media": m,
                "Alta": a,
                "Esquema": f"{b}-{m}-{a}",
            })
        band_df = pd.DataFrame(band_df_data)
        st.dataframe(band_df, width="stretch", hide_index=True)

    st.divider()

    # Display volantes
    st.subheader("Volantes Generados")

    for vol_idx, volante in enumerate(volantes):
        with st.expander(
            f"Volante #{vol_idx + 1} — {len(volante)} jugada(s) — RD${COST_PER_VOLANTE}"
        ):
            for play_idx, ticket in enumerate(volante):
                nums_str = ", ".join(f"{n:02d}" for n in ticket)
                # Phase 5: Get band distribution for this ticket
                ticket_idx = tickets.index(ticket) if ticket in tickets else -1
                if ticket_idx >= 0 and ticket_idx < len(ticket_bands_data):
                    b, m, a = ticket_bands_data[ticket_idx]
                    band_str = f" [B:{b} M:{m} A:{a}]"
                else:
                    band_str = ""
                st.write(f"**Jugada {play_idx + 1}:** {nums_str}{band_str}")

    st.divider()

    # Blindaje verification
    st.subheader("Verificacion de Blindaje")

    blindaje_ok = True
    issues = []

    for i, ticket in enumerate(tickets):
        if list(ticket) != sorted(ticket):
            blindaje_ok = False
            issues.append(f"Boleto {i+1}: no esta ordenado ascendente")
        for n in ticket:
            if n not in pool:
                blindaje_ok = False
                issues.append(f"Boleto {i+1}: numero {n} fuera del pool")
        if len(ticket) != 10:
            blindaje_ok = False
            issues.append(f"Boleto {i+1}: tamano {len(ticket)} != 10")

    ticket_set = set(tickets)
    if len(ticket_set) != len(tickets):
        blindaje_ok = False
        issues.append("Tickets duplicados detectados")

    # Phase 5: Verify band distribution per ticket
    if ticket_band_dist is not None:
        for i, ticket in enumerate(tickets):
            if i < len(ticket_bands_data):
                actual_b, actual_m, actual_a = ticket_bands_data[i]
                expected_b, expected_m, expected_a = ticket_band_dist
                if (actual_b, actual_m, actual_a) != (expected_b, expected_m, expected_a):
                    blindaje_ok = False
                    issues.append(
                        f"Boleto {i+1}: distribucion {actual_b}-{actual_m}-{actual_a} "
                        f"no coincide con {expected_b}-{expected_m}-{expected_a}"
                    )

    if blindaje_ok:
        st.success(
            ":material/check_circle: Blindaje estricto verificado: "
            "0 numeros fuera del pool, orden ascendente, "
            "0 boletos duplicados o permutados."
        )
    else:
        st.error("Problemas de blindaje detectados:")
        for issue in issues[:10]:
            st.write(f"  - {issue}")

    # Download button
    st.divider()
    st.subheader("Descargar Jugadas")

    download_lines = [
        "=" * 60,
        "SUPERKINOTV — KENO 20/80 — JUGADAS GENERADAS",
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"Pool: {', '.join(str(n) for n in pool)}",
        f"Boletos: {len(tickets)} | Volantes: {len(volantes)}",
        f"Costo Total: RD${len(volantes) * COST_PER_VOLANTE:,}",
        "=" * 60,
        "",
    ]

    for vol_idx, volante in enumerate(volantes):
        download_lines.append(f"--- VOLANTE #{vol_idx + 1} (RD${COST_PER_VOLANTE}) ---")
        for play_idx, ticket in enumerate(volante):
            nums_str = ",".join(f"{n:02d}" for n in ticket)
            # Phase 5: Include band info per ticket
            ticket_idx = tickets.index(ticket) if ticket in tickets else -1
            if ticket_idx >= 0 and ticket_idx < len(ticket_bands_data):
                b, m, a = ticket_bands_data[ticket_idx]
                download_lines.append(f"  Jugada {play_idx + 1}: {nums_str}  [{b}-{m}-{a}]")
            else:
                download_lines.append(f"  Jugada {play_idx + 1}: {nums_str}")
        download_lines.append("")

    download_lines.extend([
        "=" * 60,
        "Generado por SuperKinoTV — Analisis Determinista",
        "=" * 60,
    ])

    download_text = "\n".join(download_lines)

    st.download_button(
        label=":material/download: Descargar jugadas (.txt)",
        data=download_text,
        file_name=f"superkino_jugadas_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        type="primary",
    )

    # Verification against winning numbers
    st.divider()
    st.subheader(":material/verified: Verificar Contra Numeros Ganadores")
    st.caption("Ingresa los 20 numeros ganadores para verificar aciertos en tus boletos.")

    winning_input = st.text_area(
        "Numeros ganadores (20 numeros separados por coma)",
        placeholder="01,05,12,18,23,25,30,35,40,44,50,52,55,57,59,61,63,70,75,80",
        help="Ingresa exactamente 20 numeros del 1 al 80, separados por coma.",
        key="winning_numbers_input",
    )

    if st.button("Verificar Aciertos", type="primary", key="verify_btn"):
        try:
            winning_nums = [int(n.strip()) for n in winning_input.split(",")]
        except ValueError:
            st.error("Formato invalido: usa numeros separados por coma (ej: 1,5,12,...)")
            st.stop()

        if len(winning_nums) != 20:
            st.error(f"Se necesitan 20 numeros, se ingresaron {len(winning_nums)}.")
            st.stop()

        if not all(1 <= n <= 80 for n in winning_nums):
            st.error("Los numeros deben estar en el rango 1-80.")
            st.stop()

        if len(set(winning_nums)) != 20:
            st.error("Los numeros deben ser unicos.")
            st.stop()

        results, summary = verify_winning_numbers(tickets, winning_nums)

        st.subheader("Resumen de Verificacion")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Mejor Aciertos", f"{summary['best_aciertos']}/10")
        with col2:
            st.metric("Total Aciertos", summary["total_matches"])
        with col3:
            avg = summary["total_matches"] / summary["total_tickets"] if summary["total_tickets"] else 0
            st.metric("Promedio", f"{avg:.1f}")

        st.subheader("Distribucion de Aciertos")
        dist_cols = st.columns(6)
        for i, (tier, count) in enumerate(summary["distribution"].items()):
            with dist_cols[i]:
                st.metric(f"{tier} aciertos", count)

        st.subheader("Resultados por Volante")

        for vol_idx, volante in enumerate(volantes):
            volante_results = [r for r in results if r["ticket"] in volante]
            best_in_vol = max(r["aciertos"] for r in volante_results) if volante_results else 0
            with st.expander(f"Volante #{vol_idx + 1} — Mejor: {best_in_vol} aciertos"):
                for r in volante_results:
                    ticket_str = ", ".join(f"{n:02d}" for n in r["ticket"])
                    matching_str = ", ".join(f"{n:02d}" for n in r["matching_numbers"])

                    if r["aciertos"] >= 7:
                        icon = "🟢"
                    elif r["aciertos"] >= 5:
                        icon = "🟡"
                    else:
                        icon = "⚪"

                    st.write(f"{icon} **{r['aciertos']}/10** — {ticket_str}")
                    if r["matching_numbers"]:
                        st.caption(f"   Aciertos: {matching_str}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: BACKTESTING (Phase 6: BT-01 through BT-05)
# ═══════════════════════════════════════════════════════════════════════════════

def render_tab_backtesting(draws: List[Draw], config: Dict) -> None:
    """Render walk-forward backtesting tab."""
    st.header(":material/analytics: Backtesting Walk-Forward")
    st.markdown(
        "Simula el rendimiento de tu estrategia de wheeling contra una "
        "linea base aleatoria usando validacion walk-forward."
    )

    # --- Parameters ---
    col1, col2, col3 = st.columns(3)
    with col1:
        train_window = st.slider(
            "Ventana de entrenamiento",
            min_value=20,
            max_value=min(100, len(draws) - 2),
            value=min(config.get("window", 80), len(draws) - 2),
            help="Numero de sorteos para entrenar antes de cada prueba.",
            key="bt_train_window",
        )
    with col2:
        bt_temperature = st.slider(
            "Temperatura T (backtesting)",
            min_value=0.05,
            max_value=2.0,
            value=config.get("temperature", 1.0),
            step=0.05,
            help="Override de temperatura para backtesting. T baja = determinista, T alta = aleatorio.",
            key="bt_temperature",
        )
    with col3:
        n_tickets = st.slider(
            "Boletos por periodo",
            min_value=6,
            max_value=30,
            value=config.get("n_tickets", 18),
            help="Cantidad de boletos generados en cada periodo de prueba.",
            key="bt_n_tickets",
        )

    # Validation
    n_test_periods = len(draws) - train_window - 1
    if n_test_periods < 1:
        st.error(
            f"No hay suficientes sorteos para backtesting. "
            f"Necesita al menos {train_window + 2} sorteos, "
            f"tiene {len(draws)}."
        )
        return

    st.info(
        f"Periodos de prueba disponibles: **{n_test_periods}** "
        f"(ventana={train_window}, sorteos totales={len(draws)})"
    )

    # --- Run ---
    if st.button("Ejecutar Backtesting", key="bt_run", type="primary"):
        with st.spinner("Ejecutando simulacion walk-forward..."):
            bt_config = {**config, "window": train_window}
            results = walk_forward_backtest(
                draws, bt_config,
                temperature=bt_temperature,
                n_tickets=n_tickets,
                ticket_size=10,
            )
            st.session_state["bt_results"] = results

            # Temperature effect — computed ONCE alongside the main backtest.
            temp_values = [0.1, 0.5, 1.0, 1.5, 2.0]
            temp_results = []
            for t_val in temp_values:
                bt_config_t = {**config, "window": train_window}
                t_result = walk_forward_backtest(
                    draws, bt_config_t,
                    temperature=t_val,
                    n_tickets=n_tickets,
                    ticket_size=10,
                )
                temp_results.append({
                    "T": t_val,
                    "Tasa de acierto": t_result["hit_rate_user"],
                    "Aciertos totales": t_result["cumulative_aciertos"][-1] if t_result["cumulative_aciertos"] else 0,
                })
            st.session_state["bt_temp_results"] = temp_results
            st.session_state["bt_params_used"] = (train_window, round(float(bt_temperature), 2), n_tickets)

    results = st.session_state.get("bt_results")
    if results is None:
        st.info("Configure los parametros y presione 'Ejecutar Backtesting'.")
        return

    # Stale-parameter detection — results shown from session_state until Run is pressed.
    bt_params_used = st.session_state.get("bt_params_used")
    if bt_params_used is not None:
        current_bt = (train_window, round(float(bt_temperature), 2), n_tickets)
        if current_bt != bt_params_used:
            st.caption("Parametros cambiados — presione Ejecutar Backtesting para actualizar los resultados.")

    # --- Summary Metrics ---
    st.subheader("Resumen de Resultados")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Periodos de prueba",
            f"{results['n_test_periods']}",
        )
    with m2:
        st.metric(
            "Tasa de acierto (tu estrategia)",
            f"{results['hit_rate_user']:.1%}",
        )
    with m3:
        st.metric(
            "Tasa de acierto (hipergeometrica)",
            f"{results['hit_rate_hyper']:.1%}",
        )
    with m4:
        st.metric(
            "Tasa de acierto (Monte Carlo)",
            f"{results['hit_rate_mc']:.1%}",
        )

    # ROI calculation
    total_cost = results["total_cost"]
    total_aciertos = results["cumulative_aciertos"][-1] if results["cumulative_aciertos"] else 0
    roi = (total_aciertos * COST_PER_VOLANTE - total_cost) / total_cost if total_cost > 0 else 0

    r1, r2 = st.columns(2)
    with r1:
        st.metric(
            "Costo total (RD$)",
            f"RD${total_cost:,.0f}",
        )
    with r2:
        st.metric(
            "ROI estimado",
            f"{roi:.1%}",
            delta=f"{'Positivo' if roi > 0 else 'Negativo'}",
            delta_color="normal" if roi > 0 else "inverse",
        )

    # --- Cumulative Aciertos Chart ---
    st.subheader("Aciertos Acumulados")

    chart_data = pd.DataFrame({
        "Periodo": list(range(1, results["n_test_periods"] + 1)),
        "Tu estrategia": results["cumulative_aciertos"],
        "Hipergeometrica": results["cumulative_hyper"],
        "Monte Carlo": results["cumulative_mc"],
    })

    st.line_chart(
        chart_data.set_index("Periodo"),
    )

    # --- Temperature Effect (rendered from session_state, no recompute) ---
    st.subheader("Efecto de la Temperatura")
    st.markdown(
        "Compara como diferentes valores de T afectan el rendimiento."
    )

    temp_results = st.session_state.get("bt_temp_results")
    if temp_results:
        temp_df = pd.DataFrame(temp_results)
        st.dataframe(temp_df, width="stretch", hide_index=True)
        st.line_chart(temp_df.set_index("T")[["Tasa de acierto"]])

    # --- Per-period detail ---
    with st.expander("Detalle por periodo de prueba"):
        detail_data = []
        for r in results["results"]:
            detail_data.append({
                "Sorteo": r["test_draw"].date_iso,
                "Aciertos": r["best_aciertos"],
                "Esperado (hiper)": f"{r['hyper_expected']:.2f}",
                "Esperado (MC)": f"{r['mc_avg_aciertos']:.2f}",
            })
        detail_df = pd.DataFrame(detail_data)
        st.dataframe(detail_df, width="stretch", hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: PREDICTIVE ANALYSIS (Phase 7: BT-06)
# ═══════════════════════════════════════════════════════════════════════════════


def render_tab_predictive(draws: List[Draw], config: Dict) -> None:
    """Render predictive analysis tab with comprehensive intelligent analysis."""
    st.header(":material/auto_awesome: Analisis Predictivo")
    st.markdown(
        "Analisis inteligente que combina frecuencia, gaps, co-ocurrencia, "
        "temperatura, patrones temporales y tendencias de bandas para "
        "sugerir los numeros optimos."
    )

    # --- Parameters ---
    col1, col2 = st.columns(2)
    with col1:
        pred_window = st.slider(
            "Ventana de analisis",
            min_value=20,
            max_value=min(100, len(draws)),
            value=min(config.get("window", 80), len(draws)),
            help="Numero de sorteos recientes para el analisis predictivo.",
            key="pred_window",
        )
    with col2:
        pred_temperature = st.slider(
            "Temperatura T",
            min_value=0.05,
            max_value=2.0,
            value=config.get("temperature", 1.0),
            step=0.05,
            help="T baja = numeros frecuentes (determinista). T alta = distribucion uniforme (aleatorio).",
            key="pred_temperature",
        )

    # Validation
    if len(draws) < 10:
        st.error("Se necesitan al menos 10 sorteos para analisis predictivo.")
        return

    # --- Run Analysis ---
    if st.button("Ejecutar Analisis Predictivo", key="pred_run", type="primary"):
        with st.spinner("Calculando scores predictivos..."):
            pred_scores = compute_predictive_scores(draws, pred_window, pred_temperature)
            band_suggestion = suggest_band_distribution(draws, pred_window, pred_scores)
            ticket_recs = recommend_tickets(draws, pred_scores, band_suggestion, config)
            st.session_state["pred_scores"] = pred_scores
            st.session_state["pred_band"] = band_suggestion
            st.session_state["pred_tickets"] = ticket_recs

            # Co-occurrence matrix — computed ONCE here (used by expander later).
            cooc_matrix = compute_cooccurrence_matrix(draws, pred_window)
            st.session_state["pred_cooc"] = cooc_matrix
            st.session_state["pred_params_used"] = (pred_window, round(float(pred_temperature), 2))

    pred_scores = st.session_state.get("pred_scores")
    band_suggestion = st.session_state.get("pred_band")
    ticket_recs = st.session_state.get("pred_tickets")

    if pred_scores is None:
        st.info("Configure los parametros y presione 'Ejecutar Analisis Predictivo'.")
        return

    # Stale-parameter detection — results shown from session_state until Run is pressed.
    pred_params_used = st.session_state.get("pred_params_used")
    if pred_params_used is not None:
        current_pred = (pred_window, round(float(pred_temperature), 2))
        if current_pred != pred_params_used:
            st.caption("Parametros cambiados — presione Ejecutar Analisis Predictivo para actualizar los resultados.")

    # --- Dashboard Metrics ---
    st.subheader("Dashboard de Confianza")

    # Top 5 numbers by score
    top5 = sorted(pred_scores["number_scores"], key=lambda x: x["score"], reverse=True)[:5]
    m1, m2, m3, m4, m5 = st.columns(5)
    for i, (col, item) in enumerate(zip([m1, m2, m3, m4, m5], top5)):
        with col:
            st.metric(
                f"Top {i + 1}",
                f"{item['number']:02d}",
                f"Score: {item['score']:.0f}",
            )

    # Band distribution suggestion
    st.subheader("Sugerencia de Distribucion")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        dist = band_suggestion["suggested_distribution"]
        st.metric(
            "Distribucion Sugerida",
            f"{dist[0]}-{dist[1]}-{dist[2]}",
            "Baja-Media-Alta",
        )
    with b2:
        st.metric(
            "Confianza",
            f"{band_suggestion['confidence']:.0f}%",
        )
    with b3:
        total_score = ticket_recs["total_score"]
        st.metric(
            "Score Promedio",
            f"{total_score:.1f}",
        )
    with b4:
        st.metric(
            "Boletos Recomendados",
            f"{len(ticket_recs['recommended_tickets'])}",
        )

    # --- Number Scoring Table ---
    st.subheader("Scores por Numero")

    scoring_data = []
    for item in pred_scores["number_scores"]:
        scoring_data.append({
            "Numero": f"{item['number']:02d}",
            "Score Total": f"{item['score']:.1f}",
            "Frecuencia": f"{item['factors']['frequency']:.2f}",
            "Gap": f"{item['factors']['gap']:.2f}",
            "Co-ocurrencia": f"{item['factors']['cooccurrence']:.2f}",
            "Recencia": f"{item['factors']['recency']:.2f}",
            "Temporal": f"{item['factors']['temporal']:.2f}",
            "Tendencia": f"{item['factors']['band_trend']:.2f}",
        })

    scoring_df = pd.DataFrame(scoring_data)

    st.markdown("**Top 20 numeros por score:**")
    st.dataframe(scoring_df.head(20), hide_index=True)

    with st.expander("Ver todos los 80 numeros"):
        st.dataframe(scoring_df, hide_index=True)

    # --- Band Analysis Detail ---
    st.subheader("Analisis por Franja")

    with st.expander("Detalle de analisis por franja", expanded=False):
        for band_name, band_data in band_suggestion["band_analysis"].items():
            trend_icon = "📈" if band_data["trend"] == "up" else "📉" if band_data["trend"] == "down" else "➡️"
            hot_cold = "🔥 Hot" if band_data["hot_cold"] == "hot" else "❄️ Cold" if band_data["hot_cold"] == "cold" else "⚖️ Neutral"
            st.markdown(
                f"**{band_name}**: Frecuencia {band_data['frequency']:.1%} "
                f"| {trend_icon} {band_data['trend']} "
                f"| {hot_cold}"
            )

        st.markdown("**Razonamiento:**")
        st.markdown(band_suggestion["reasoning"])

        if band_suggestion["alternative_distributions"]:
            st.markdown("**Distribuciones alternativas:**")
            alt_data = []
            for alt in band_suggestion["alternative_distributions"]:
                alt_data.append({
                    "Distribucion": f"{alt['dist'][0]}-{alt['dist'][1]}-{alt['dist'][2]}",
                    "Confianza": f"{alt['confidence']:.0f}%",
                    "Razon": alt["reason"],
                })
            st.dataframe(pd.DataFrame(alt_data), hide_index=True)

    # --- Temporal Patterns ---
    st.subheader("Patrones Temporales")

    with st.expander("Detalle de patrones temporales", expanded=False):
        temporal = pred_scores["temporal_patterns"]

        # Day of week patterns
        st.markdown("**Frecuencia por dia de la semana:**")
        day_names = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        for day_idx in range(7):
            if day_idx in temporal["day_of_week_freq"]:
                top3 = sorted(
                    temporal["day_of_week_freq"][day_idx].items(),
                    key=lambda x: x[1], reverse=True,
                )[:3]
                top3_str = ", ".join([f"{n:02d} ({f:.1%})" for n, f in top3])
                st.markdown(f"- **{day_names[day_idx]}**: {top3_str}")

        # Band cyclical patterns
        st.markdown("**Patrones ciclicos:**")
        for band, is_cyclical in temporal["band_cyclical"].items():
            if is_cyclical:
                st.markdown(f"- **{band}**: Patron ciclico detectado")

        # Recent band shift
        st.markdown("**Cambios recientes (ultimos 10 vs anteriores 10):**")
        for band, shift in temporal["recent_band_shift"].items():
            direction = "↑" if shift > 0 else "↓" if shift < 0 else "→"
            st.markdown(f"- **{band}**: {direction} {shift:+.1%}")

    # --- Top Co-occurring Pairs ---
    st.subheader("Pares con Mayor Co-ocurrencia")

    with st.expander("Detalle de co-ocurrencias", expanded=False):
        if pred_scores["cooccurrence_top_pairs"]:
            pairs_data = []
            for a, b, score in pred_scores["cooccurrence_top_pairs"][:20]:
                pairs_data.append({
                    "Par": f"{a:02d}-{b:02d}",
                    "Co-ocurrencia": f"{score:.3f}",
                })
            st.dataframe(pd.DataFrame(pairs_data), hide_index=True)
        else:
            st.info("No hay suficientes datos para calcular co-ocurrencias.")

    # --- Recommended Tickets ---
    st.subheader("Boletos Recomendados")

    if ticket_recs["recommended_tickets"]:
        for i, rec in enumerate(ticket_recs["recommended_tickets"]):
            with st.container(border=True):
                cols = st.columns([2, 3])
                with cols[0]:
                    st.markdown(f"**Boleto {i + 1}**")
                    st.markdown(f"Numeros: `{' '.join(f'{n:02d}' for n in rec['numbers'])}`")
                    st.markdown(f"Franja: {rec['band_dist'][0]}-{rec['band_dist'][1]}-{rec['band_dist'][2]}")
                    st.metric("Score", f"{rec['score']:.1f}")
                with cols[1]:
                    st.markdown("**Razonamiento:**")
                    st.markdown(rec["reasoning"])
    else:
        st.warning("No se pudieron generar boletos recomendados con los parametros actuales.")

    # --- Co-occurrence Heatmap ---
    with st.expander("Matriz de co-ocurrencia (top 20 numeros)", expanded=False):
        cooc_matrix = st.session_state.get("pred_cooc")
        if cooc_matrix is not None:
            top20_nums = [item["number"] for item in pred_scores["number_scores"][:20]]
            subset_cooc = cooc_matrix.loc[top20_nums, top20_nums]
            st.dataframe(
                subset_cooc.style.background_gradient(cmap="YlOrRd"),
            )


# ═══════════════════════════════════════════════════════════════════════════════
# DATA INGESTION UI
# ═══════════════════════════════════════════════════════════════════════════════

def render_data_ingestion() -> List[Draw]:
    """Render data ingestion UI and return draws from session state.
    
    Handles:
    - D-12: Data persists across all tabs via session_state.draws
    - D-13: Replace confirmation when uploading new file while data exists
    - D-14: Dual source detection (file + text area both have content)
    - D-15: Combine both sources with dedup by date
    """
    st.subheader(":material/upload: Carga de Datos Historicos")

    col_upload, col_paste = st.columns([1, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Subir archivo (.txt o .csv)",
            type=["txt", "csv"],
            help="Formato: DD/MM/AAAA,N1,N2,...,N20 por linea",
        )

    with col_paste:
        text_area = st.text_area(
            "O pegar historial directamente",
            height=150,
            placeholder="21/04/2026,1,5,6,14,30,34,40,42,43,44,46,48,52,55,61,67,69,73,76,78",
            help="Una linea por sorteo: DD/MM/AAAA,N1,N2,...,N20",
        )

    has_file = uploaded_file is not None
    has_text = bool(text_area.strip())
    has_existing = "draws" in st.session_state and len(st.session_state.draws) > 0

    # --- D-14: Dual source detection ---
    if has_file and has_text:
        st.warning(":material/warning: Se detectaron dos fuentes de datos. &iquest;Cual desea usar?")
        source_choice = st.radio(
            "Fuente de datos",
            options=["Solo archivo", "Solo texto", "Combinar ambos"],
            label_visibility="collapsed",
            horizontal=True,
        )
        if source_choice == "Solo archivo":
            lines = uploaded_file.getvalue().decode("utf-8", errors="replace").splitlines()
        elif source_choice == "Solo texto":
            lines = text_area.strip().splitlines()
        else:  # Combinar ambos — D-15
            file_lines = uploaded_file.getvalue().decode("utf-8", errors="replace").splitlines()
            text_lines = text_area.strip().splitlines()
            lines = file_lines + text_lines
    elif has_file:
        # --- D-13: Replace confirmation ---
        if has_existing:
            st.warning(":material/warning: &iquest;Reemplazar datos actuales?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Si, reemplazar", type="primary", key="confirm_replace"):
                    st.session_state["_replace_confirmed"] = True
            with col_no:
                if st.button("No, cancelar", key="cancel_replace"):
                    st.session_state["_replace_confirmed"] = False

            if st.session_state.get("_replace_confirmed"):
                lines = uploaded_file.getvalue().decode("utf-8", errors="replace").splitlines()
            else:
                # Show existing data info, don't replace
                st.info(f":material/info: {len(st.session_state.draws)} sorteos cargados existentes.")
                return st.session_state.draws
        else:
            lines = uploaded_file.getvalue().decode("utf-8", errors="replace").splitlines()
    elif has_text:
        lines = text_area.strip().splitlines()
    else:
        # No input — show empty state
        if has_existing:
            return st.session_state.draws
        st.info(
            "Carga un archivo .txt/.csv o pega las lineas del historial para comenzar. "
            "Formato esperado: `DD/MM/AAAA,n1,n2,...,n20` (20 numeros, 1-80, unicos)."
        )
        st.markdown("---")
        st.markdown(
            "**Datos de referencia:** 120 sorteos historicos (21/04/2026 - 19/08/2026). "
            "Puedes cargar tu archivo `SuperKinoTV.txt` o pegar los datos directamente."
        )
        return []

    # --- Process data (strict: all-or-nothing per D-02) ---
    draws, errors = ingest_lines(lines)

    if errors:
        # D-02: NO data loaded when errors exist
        with st.expander(f":material/error: {len(errors)} lineas con errores"):
            for line_num, err_msg, raw_line in errors:
                st.write(f"**Linea {line_num}:** {err_msg}")
                st.code(f"{raw_line}", language=None)
        return []

    if draws:
        # D-12: Persist in session state
        st.session_state.draws = draws
        st.success(f":material/check_circle: {len(draws)} sorteos validos cargados.")
        return draws

    return []


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main Streamlit application."""
    st.title(":material/casino: SuperKinoTV - Keno 20/80")
    st.markdown(
        "**Analisis y generacion de boletos** para el juego Keno 20/80 (SuperKino TV). "
        "Toda la logica es 100% deterministica - ejecutada en Python backend."
    )

    # --- Data Ingestion (D-12: persists via session state) ---
    draws = render_data_ingestion()

    if not draws:
        return

    # --- Sidebar Controls ---
    config = render_sidebar(len(draws))

    # D-09: Block tab rendering if band distribution is invalid
    if not config.get("band_valid", True):
        st.warning(":material/block: Corrija la distribucion por franja antes de continuar.")
        return

    # --- Tabs ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ":material/table_chart: Matrices Intermedias",
        ":material/query_stats: Pool Dinamico",
        ":material/style: Volantes & Reduccion Combinatoria",
        ":material/analytics: Backtesting",
        ":material/auto_awesome: Analisis Predictivo",
    ])

    with tab1:
        render_tab_matrices(draws, config)

    with tab2:
        render_tab_pool(draws, config)

    with tab3:
        render_tab_tickets(draws, config)

    with tab4:
        render_tab_backtesting(draws, config)

    with tab5:
        render_tab_predictive(draws, config)


if __name__ == "__main__":
    main()
