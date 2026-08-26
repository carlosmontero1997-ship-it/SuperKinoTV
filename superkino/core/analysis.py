"""Análisis matricial sobre un DrawHistory — cálculos puros, sin streamlit."""

from __future__ import annotations

from typing import Dict, List, Tuple

from .models import DrawHistory
from .ingest import (
    compute_presence_matrix,
    compute_gaps,
    compute_positional_stats,
    compute_pair_lift,
    compute_sums_parity_decades,
)


# ── Helpers para formatear resultados en diccionados amigables ────────────

def format_freq_table(history: DrawHistory, window: int = 100) -> Dict[str, object]:
    """Tabla de frecuencias calientes/frías sobre la ventana."""
    P, frec = compute_presence_matrix(history, window)
    expected = window * 20 / 80

    # Ordenar por frecuencia descendente
    numbered = [(n + 1, f) for n, f in enumerate(frec)]
    numbered.sort(key=lambda x: x[1], reverse=True)

    hot = numbered[:10]  # top 10
    cold = numbered[-10:]  # bottom 10

    return {
        "window": window,
        "expected_per_number": expected,
        "hot_numbers": [(num, freq) for num, freq in hot],
        "cold_numbers": [(num, freq) for num, freq in cold],
    }


def format_gap_table(history: DrawHistory, window: int = 100) -> Dict[str, object]:
    """Tabla de atrasos (sorteos desde última aparición)."""
    P, _ = compute_presence_matrix(history, window)
    gaps = compute_gaps(P, window)

    # Ordenar por atraso descendente (los más "vencidos" primero)
    numbered = [(n + 1, g) for n, g in enumerate(gaps)]
    numbered.sort(key=lambda x: x[1], reverse=True)

    return {
        "window": window,
        "gaps": numbered,  # list of (number, gap)
        "max_gap": max(gaps),
        "numbers_never_in_window": [n for n, g in enumerate(gaps) if g == window],
    }


def format_positional_summary(history: DrawHistory, window: int = 100) -> dict:
    """Resumen posicional empírico vs teórico."""
    stats = compute_positional_stats(history, window)
    n = stats["n"]

    # Desviación empírica - teórica por posición
    deviations = [
        emp - theo
        for emp, theo in zip(stats["empirical_means"], stats["theoretical_means"])
    ]

    return {
        "window": window,
        "n": n,
        "empirical_means": stats["empirical_means"],
        "theoretical_means": stats["theoretical_means"],
        "deviations": deviations,
        "per_number_theoretical": stats["per_number_theoretical"],
    }


def format_lift_table(history: DrawHistory, window: int = 100, top: int = 20) -> dict:
    """Lift de pares más destacable (mayor y menor)."""
    observed, lift = compute_pair_lift(history._draws[-window:].__class__.__name__)  # fallback
    # Actually need the draws... let me restructure
    pass


# ── APIs públicas para la UI ────────────────────────────────────────────

def analyze_window(history: DrawHistory, window: int = 100) -> dict:
    """Ejecutar todo el análisis sobre la ventana especificada y devolver un dict
    listo para ser consumido por la capa Streamlit."""
    P, frec = compute_presence_matrix(history, window)
    gaps = compute_gaps(P, window)
    pos = compute_positional_stats(history, window)
    sums_pdc = compute_sums_parity_decades(history, window)

    observed, lift = compute_pair_lift(P, window)

    return {
        "presence_matrix": P,  # 0/1 W×80
        "frequencies": frec,
        "expected_per_number": window * 20 / 80,
        "gaps": gaps,
        "positional": pos,
        "sums": sums_pdc["sums"],
        "sum_avg": sums_pdc["sum_avg"],
        "parity_counts": sums_pdc["parity_counts"],
        "decade_counts": sums_pdc["decade_counts"],
        "pair_lift_observed": observed,
        "pair_lift": lift,
    }