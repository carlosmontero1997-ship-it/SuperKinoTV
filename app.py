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

BAND_PRESETS = {
    "Equilibrada Dinámica": None,  # calculated dynamically
    "4-3-3": (4, 3, 3),
    "3-4-3": (3, 4, 3),
    "3-3-4": (3, 3, 4),
    "Personalizada": None,
}

COST_PER_VOLANTE = 75  # RD$


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


def ingest_lines(lines: List[str]) -> Tuple[List[Draw], List[Tuple[int, str]]]:
    """Parse multiple lines. Returns (draws, errors)."""
    draws: List[Draw] = []
    errors: List[Tuple[int, str]] = []
    seen_dates: set = set()

    for idx, raw in enumerate(lines):
        ok, draw, err = parse_line(raw)
        if not ok:
            errors.append((idx, err))
            continue
        if draw.date_iso in seen_dates:
            errors.append((idx, f"Fecha duplicada: {draw.date_iso}"))
            continue
        seen_dates.add(draw.date_iso)
        draws.append(draw)

    draws.sort(key=lambda d: d.date_iso)
    return draws, errors


def get_draws_from_input(uploaded_file, text_area: str) -> Tuple[List[Draw], List[Tuple[int, str]]]:
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
    """100x20 intermediate matrix: each row is a draw, columns are sorted positions."""
    subset = draws[-window:] if len(draws) >= window else draws
    rows = []
    for d in subset:
        rows.append(list(d.numbers))
    df = pd.DataFrame(rows, columns=[f"P{i+1}" for i in range(20)])
    df.index = [f"S{i+1}" for i in range(len(subset))]
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
) -> List[Tuple[int, ...]]:
    """Deterministic wheeling reduction algorithm.

    Generates n_tickets combinations of ticket_size numbers each,
    drawn from the pool using a balanced covering approach.

    Algorithm:
    1. Generate all C(pool_size, ticket_size) combinations if feasible
    2. Score each by coverage (how many unique pairs/triples it covers)
    3. Greedily select n_tickets that maximize total coverage
    4. Enforce strict blindaje: ascending sort, 0 duplicates
    """
    pool_sorted = sorted(pool)
    pool_size = len(pool_sorted)

    if pool_size < ticket_size:
        # Pool too small — pad with smallest available numbers
        extra = [n for n in range(1, 81) if n not in pool_sorted]
        pool_sorted = sorted(pool_sorted + extra[: ticket_size - pool_size])
        pool_size = len(pool_sorted)

    # Generate candidate combinations
    max_candidates = min(5000, math.comb(pool_size, ticket_size))

    if max_candidates <= n_tickets:
        # Fewer candidates than tickets — use all + fill
        candidates = list(itertools.combinations(pool_sorted, ticket_size))
        # Pad if needed by repeating with small variations
        while len(candidates) < n_tickets:
            base = candidates[len(candidates) % max(candidates.__len__(), 1)]
            # Try swapping one element
            for alt in pool_sorted:
                if alt not in base:
                    new_ticket = tuple(sorted((alt,) + tuple(x for x in base if True)))
                    # Replace the smallest with alt
                    new_ticket = tuple(sorted(list(base[:-1]) + [alt]))
                    if new_ticket not in candidates and len(new_ticket) == ticket_size:
                        candidates.append(new_ticket)
                        break
            else:
                break
    else:
        # Many candidates — use systematic sampling
        step = max(1, math.comb(pool_size, ticket_size) // max_candidates)
        candidates = []
        for i, combo in enumerate(itertools.combinations(pool_sorted, ticket_size)):
            if i % step == 0:
                candidates.append(combo)
            if len(candidates) >= max_candidates:
                break

    # Greedy coverage selection
    selected: List[Tuple[int, ...]] = []
    covered_pairs: set = set()

    for _ in range(n_tickets):
        best_combo = None
        best_new_pairs = -1

        for combo in candidates:
            if combo in selected:
                continue
            # Count new pairs this combo would cover
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
            for i in range(len(best_combo)):
                for j in range(i + 1, len(best_combo)):
                    covered_pairs.add((best_combo[i], best_combo[j]))
        else:
            break

    # Enforce strict blindaje
    result = []
    seen = set()
    for ticket in selected:
        t = tuple(sorted(ticket))
        # Verify all numbers in pool
        t = tuple(n for n in t if n in pool_sorted)
        if len(t) < ticket_size:
            continue
        t = tuple(sorted(t[:ticket_size]))
        if t not in seen:
            seen.add(t)
            result.append(t)

    return result[:n_tickets]


def group_into_volantes(tickets: List[Tuple[int, ...]]) -> List[List[Tuple[int, ...]]]:
    """Group tickets into volantes of 3 plays each."""
    volantes = []
    for i in range(0, len(tickets), 3):
        volante = tickets[i : i + 3]
        volantes.append(volante)
    return volantes


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar(n_draws: int) -> Dict:
    """Render sidebar controls and return configuration dict."""
    st.sidebar.header("⚙️ Configuracion")

    # Window slider
    max_window = min(100, n_draws)
    window = st.sidebar.slider(
        "Ventana de sorteos (retroactivos)",
        min_value=10,
        max_value=max_window,
        value=max_window,
        help="Maximo 100 sorteos retroactivos desde el ultimo sorteo cargado.",
    )

    st.sidebar.divider()

    # Pool size
    pool_size = st.sidebar.slider(
        "Tamano del Pool Dinamico",
        min_value=15,
        max_value=30,
        value=20,
        help="Cantidad de numeros en el pool generado automaticamente.",
    )

    # Ticket quantity
    n_tickets = st.sidebar.slider(
        "Cantidad de Boletos (Wheeling)",
        min_value=6,
        max_value=30,
        value=18,
        help="Numero de combinaciones a generar via reduccion combinatoria.",
    )

    st.sidebar.divider()

    # Band distribution
    st.sidebar.subheader("Distribucion por Franja")
    st.sidebar.caption("Baja: 01-26 | Media: 27-54 | Alta: 55-80")

    preset = st.sidebar.selectbox(
        "Preset de distribucion",
        options=list(BAND_PRESETS.keys()),
        index=0,
    )

    band_dist = None
    custom_input = None

    if preset == "Equilibrada Dinamica":
        band_dist = None  # Will be calculated dynamically
        st.sidebar.info("Distribucion proporcional calculada automaticamente.")
    elif preset == "Personalizada":
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            low = st.number_input("Baja", min_value=0, max_value=pool_size, value=math.ceil(pool_size * 26 / 80))
        with col2:
            mid = st.number_input("Media", min_value=0, max_value=pool_size, value=math.ceil(pool_size * 28 / 80))
        with col3:
            high = st.number_input("Alta", min_value=0, max_value=pool_size, value=pool_size - low - mid)
        total = low + mid + high
        if total != pool_size:
            st.sidebar.warning(f"Total ({total}) != Pool ({pool_size}). Se ajustara automaticamente.")
        band_dist = (low, mid, high)
    else:
        band_dist = BAND_PRESETS[preset]
        st.sidebar.write(f" Distribucion: **{band_dist[0]}-{band_dist[1]}-{band_dist[2]}**")

    return {
        "window": window,
        "pool_size": pool_size,
        "n_tickets": n_tickets,
        "band_dist": band_dist,
        "preset": preset,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: MATRICES INTERMEDIAS
# ═══════════════════════════════════════════════════════════════════════════════

def render_tab_matrices(draws: List[Draw], config: Dict):
    """Render the intermediate matrices tab."""
    st.header("Matrices Intermedias")

    window = config["window"]

    # 1. 100x20 Intermediate Matrix
    st.subheader(f"Matriz Intermedia {window} x 20")
    st.caption(
        f"Cada fila es un sorteo ordenado, columnas P1-P20 son las posiciones "
        f"(menor a mayor). Mostrando ultimos {window} sorteos."
    )

    df_inter = compute_intermediate_matrix(draws, window)
    st.dataframe(df_inter, use_container_width=True, height=400)

    st.divider()

    # 2. 10x10 Positional Frequency Matrix
    st.subheader("Matriz 10 x 10 de Frecuencias Posicionales")
    st.caption(
        "Agrupada por pares de carriles adyacentes: "
        "C1=(B1,B2), C2=(B3,B4), ..., C10=(B19,B20). "
        "Cada celda cuenta cuantos numeros de cada franja aparecen en esas posiciones."
    )

    df_freq = compute_positional_frequency_matrix(draws, window)
    st.dataframe(df_freq, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Instala plotly para visualizaciones: `pip install plotly`")


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

    # Pool display
    st.subheader(f"Pool Dinamico — {len(pool)} Numeros")

    # Display pool as a nice grid
    cols = st.columns(10)
    for i, num in enumerate(pool):
        col = cols[i % 10]
        with col:
            if num in BAND_LOW:
                st.metric(label=f"N{num}", value=num, delta="Baja", delta_color="off")
            elif num in BAND_MID:
                st.metric(label=f"N{num}", value=num, delta="Media", delta_color="off")
            else:
                st.metric(label=f"N{num}", value=num, delta="Alta", delta_color="off")

    st.divider()

    # Band metrics
    st.subheader("Metricas por Franja")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Baja (01-26)", band_counts["Baja (01-26)"])
    with col2:
        st.metric("Media (27-54)", band_counts["Media (27-54)"])
    with col3:
        st.metric("Alta (55-80)", band_counts["Alta (55-80)"])

    # Distribution bar
    dist_df = pd.DataFrame(
        list(band_counts.items()), columns=["Franja", "Cantidad"]
    )
    st.bar_chart(dist_df.set_index("Franja"))

    # Ranking table
    st.subheader("Ranking de Numeros por Frecuencia + Co-ocurrencia")
    ranked = compute_frequency_ranking(draws, window)
    ranked_in_pool = [(n, s, f) for n, s, f in ranked if n in pool]
    df_ranked = pd.DataFrame(
        ranked_in_pool, columns=["Numero", "Score", "Frecuencia"]
    )
    df_ranked.index = range(1, len(df_ranked) + 1)
    df_ranked.index.name = "Rank"
    st.dataframe(df_ranked, use_container_width=True)


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

    # Execute wheeling
    if st.button("Generar Boletos", type="primary", key="gen_tickets"):
        with st.spinner("Ejecutando reduccion combinatoria determinista..."):
            tickets = wheeling_reduction(pool, n_tickets, ticket_size=10)

        if not tickets:
            st.error("No se pudieron generar boletos. Verifica el pool y parametros.")
            return

        volantes = group_into_volantes(tickets)

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

        st.divider()

        # Display volantes
        st.subheader("Volantes Generados")

        for vol_idx, volante in enumerate(volantes):
            vol_cost = len(volante) * (COST_PER_VOLANTE // 3)
            with st.expander(
                f"Volante #{vol_idx + 1} — {len(volante)} jugada(s) — RD${COST_PER_VOLANTE}"
            ):
                for play_idx, ticket in enumerate(volante):
                    nums_str = ", ".join(f"{n:02d}" for n in ticket)
                    st.write(f"**Jugada {play_idx + 1}:** {nums_str}")

        st.divider()

        # Blindaje verification
        st.subheader("Verificacion de Blindaje")

        blindaje_ok = True
        issues = []

        for i, ticket in enumerate(tickets):
            # Check ascending order
            if list(ticket) != sorted(ticket):
                blindaje_ok = False
                issues.append(f"Boleto {i+1}: no esta ordenado ascendente")
            # Check all in pool
            for n in ticket:
                if n not in pool:
                    blindaje_ok = False
                    issues.append(f"Boleto {i+1}: numero {n} fuera del pool")
            # Check size
            if len(ticket) != 10:
                blindaje_ok = False
                issues.append(f"Boleto {i+1}: tamano {len(ticket)} != 10")

        # Check duplicates
        ticket_set = set(tickets)
        if len(ticket_set) != len(tickets):
            blindaje_ok = False
            issues.append(f"Tickets duplicados detectados")

        if blindaje_ok:
            st.success(
                f"✓ Blindaje estricto verificado: "
                f"0 numeros fuera del pool, orden ascendente, "
                f"0 boletos duplicados o permutados."
            )
        else:
            st.error("Problemas de blindaje detectados:")
            for issue in issues[:10]:
                st.write(f"  - {issue}")

        # Download button
        st.divider()
        st.subheader("Descargar Jugadas")

        download_lines = []
        download_lines.append("=" * 60)
        download_lines.append("SUPERKINOTV — KENO 20/80 — JUGADAS GENERADAS")
        download_lines.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        download_lines.append(f"Pool: {', '.join(str(n) for n in pool)}")
        download_lines.append(f"Boletos: {len(tickets)} | Volantes: {len(volantes)}")
        download_lines.append(f"Costo Total: RD${len(volantes) * COST_PER_VOLANTE:,}")
        download_lines.append("=" * 60)
        download_lines.append("")

        for vol_idx, volante in enumerate(volantes):
            download_lines.append(f"--- VOLANTE #{vol_idx + 1} (RD${COST_PER_VOLANTE}) ---")
            for play_idx, ticket in enumerate(volante):
                nums_str = ",".join(f"{n:02d}" for n in ticket)
                download_lines.append(f"  Jugada {play_idx + 1}: {nums_str}")
            download_lines.append("")

        download_lines.append("=" * 60)
        download_lines.append("Generado por SuperKinoTV — Analisis Determinista")
        download_lines.append("=" * 60)

        download_text = "\n".join(download_lines)

        st.download_button(
            label="📥 Descargar jugadas (.txt)",
            data=download_text,
            file_name=f"superkino_jugadas_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            type="primary",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main Streamlit application."""
    st.title("🎰 SuperKinoTV — Keno 20/80")
    st.markdown(
        "**Analisis y generacion de boletos** para el juego Keno 20/80 (SuperKino TV). "
        "Toda la logica es 100% deterministica — ejecutada en Python backend."
    )

    # ── Data Ingestion ────────────────────────────────────────────────
    st.subheader("📂 Carga de Datos Historicos")

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

    # Process data
    draws: List[Draw] = []
    errors: List[Tuple[int, str]] = []

    if uploaded_file is not None or text_area.strip():
        draws, errors = get_draws_from_input(uploaded_file, text_area)

        if draws:
            st.success(f"✓ {len(draws)} sorteos validos cargados.")

        if errors:
            with st.expander(f"⚠ {len(errors)} lineas con errores"):
                for idx, err in errors:
                    st.write(f"Linea {idx + 1}: {err}")

    if not draws:
        st.info(
            "Carga un archivo .txt/.csv o pega las lineneas del historial para comenzar. "
            "Formato esperado: `DD/MM/AAAA,n1,n2,...,n20` (20 numeros, 1-80, unicos)."
        )

        # Show sample data info
        st.markdown("---")
        st.markdown(
            "**Datos de referencia:** 120 sorteos historicos (21/04/2026 – 19/08/2026). "
            "Puedes cargar tu archivo `SuperKinoTV.txt` o pegar los datos directamente."
        )
        return

    # ── Sidebar Controls ──────────────────────────────────────────────
    config = render_sidebar(len(draws))

    # ── Tabs ──────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📊 Matrices Intermedias",
        "🎯 Pool Dinamico",
        "🎟️ Volantes & Reduccion Combinatoria",
    ])

    with tab1:
        render_tab_matrices(draws, config)

    with tab2:
        render_tab_pool(draws, config)

    with tab3:
        render_tab_tickets(draws, config)


if __name__ == "__main__":
    main()
