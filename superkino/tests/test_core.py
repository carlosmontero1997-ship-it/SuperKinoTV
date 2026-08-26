"""Tests unitarios para el núcleo de SuperKino Análisis."""

import sys
import os

# Añadir superkino al path relativo al directorio del test
test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(test_dir, "..", ".."))

import pytest

import numpy as np

from core.models import Draw, DrawHistory
from core.ingest import ingest_lines
from core.analysis import (
    compute_presence_matrix, compute_gaps, compute_positional_stats,
    compute_pair_lift,
)
from core.scoring import individual_score, generate_combinations, ticket_explainer


# ── Models ─────────────────────────────────────────────────────────────

def test_draw_creation():
    d = Draw(date_iso="2026-04-21", numbers=(1, 5, 6, 14, 30, 34, 40, 42, 43, 44, 46, 48, 52, 55, 61, 67, 69, 73, 76, 78))
    assert d.date_iso == "2026-04-21"
    assert len(d.numbers) == 20
    assert all(1 <= n <= 80 for n in d.numbers)


def test_draw_invalid_count():
    with pytest.raises(ValueError):
        Draw(date_iso="2026-04-21", numbers=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19))


def test_draw_duplicate():
    with pytest.raises(ValueError):
        Draw(date_iso="2026-04-21", numbers=(1, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20))


# ── DrawHistory ────────────────────────────────────────────────────────

def test_history_from_validated_lines():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "22/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
    ]
    hist, probs = DrawHistory.from_validated_lines(lines)
    assert hist.count == 2
    assert len(probs) == 0


def test_history_duplicate_date():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "21/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,18,19,20",
    ]
    hist, probs = DrawHistory.from_validated_lines(lines, reject_duplicates=True)
    assert hist.count == 1
    assert len(probs) == 1


# ── Ingesta ────────────────────────────────────────────────────────────

def test_ingest_lines():
    lines = [
        "21/04/2026,1,5,6,14,30,34,40,42,43,44,46,48,52,55,61,67,69,73,76,78",
    ]
    hist, probs = ingest_lines(lines)
    assert hist.count == 1
    assert len(probs) == 0


# ── Análisis ───────────────────────────────────────────────────────────

def test_presence_matrix():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "22/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
    ]
    hist, _ = DrawHistory.from_validated_lines(lines)
    P, frec = compute_presence_matrix(hist, 2)
    assert len(P) == 2
    assert len(P[0]) == 80
    assert frec[0] == 1


def test_gaps():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "22/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
    ]
    hist, _ = DrawHistory.from_validated_lines(lines)
    P, _ = compute_presence_matrix(hist, 2)
    gaps = compute_gaps(P, 2)
    assert gaps[0] == 1


def test_positional_stats():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "22/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
    ]
    hist, _ = DrawHistory.from_validated_lines(lines)
    stats = compute_positional_stats(hist, 2)
    assert len(stats["empirical_means"]) == 20
    assert len(stats["theoretical_means"]) == 20
    for j, theo in enumerate(stats["theoretical_means"], start=1):
        expected = j * 81 / 21
        assert abs(stats["theoretical_means"][j - 1] - expected) < 0.01


def test_pair_lift():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "22/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
    ]
    from core.analysis import compute_presence_matrix, compute_pair_lift
    hist, _ = DrawHistory.from_validated_lines(lines)
    P, _ = compute_presence_matrix(hist, 2)
    observed, lift = compute_pair_lift(P, 2)
    assert len(observed) == 80
    assert len(lift) == 80
    # Verificar simetría
    for i in range(80):
        assert observed[i][i] == 0
        for j in range(80):
            assert observed[i][j] == observed[j][i], f"Falla simetría en [{i},{j}]"


# ── Scoring ────────────────────────────────────────────────────────────

def test_individual_score():
    # La firma usa argumentos posicionales: number, freq, freq_window, gap, gap_window, /
    # y keyword-only: w_freq, w_gap, w_pos
    s = individual_score(5, 10, 20, 0, 20)
    assert 0 <= s <= 1


def test_generate_combinations():
    import numpy as np
    # La firma usa argumentos posicionales: scores, temperature=1.0, n_combinaciones=10, rng_seed=None, /
    combos = generate_combinations(np.ones(80), 1.0, 5, 42)
    assert len(combos) == 5
    for numbers, score_total in combos:
        assert len(numbers) == 10
        assert all(1 <= n <= 80 for n in numbers)
    # Reproducibilidad
    combos2 = generate_combinations(np.ones(80), 1.0, 5, 42)
    assert combos == combos2


def test_ticket_explainer():
    numbers = (1, 5, 10, 15, 20, 25, 30, 35, 40, 45)
    scores = np.array([0.5] * 80)
    explainer = ticket_explainer(numbers, scores)
    assert explainer["score_total"] == sum(0.5 for _ in numbers)
    assert len(explainer["component_breakdown"]) == 10


def test_lift_full():
    lines = [
        "21/04/2026,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20",
        "22/04/2026,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
    ]
    from core.analysis import compute_presence_matrix, compute_pair_lift
    hist, _ = DrawHistory.from_validated_lines(lines)
    P, _ = compute_presence_matrix(hist, 2)
    observed, lift = compute_pair_lift(P, 2)
    assert len(observed) == 80
    assert len(lift) == 80
    for i in range(80):
        assert observed[i][i] == 0
        for j in range(80):
            assert observed[i][j] == observed[j][i]