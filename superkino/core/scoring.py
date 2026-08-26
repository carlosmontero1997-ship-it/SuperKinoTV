"""Scoring de números y generación de combinaciones con temperatura."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .analysis import compute_positional_stats


# ── Score individual ponderado ──────────────────────────────────────────

def individual_score(
    number: int,
    freq: int,
    freq_window: int,
    gap: int,
    gap_window: int,
    pos_idx: Optional[float] = None,
    /,
    *,
    w_freq: float = 0.4,
    w_gap: float = 0.3,
    w_pos: float = 0.3,
) -> float:
    """Score individual de un número 1-80.

    score = w_freq * f_norm + w_gap * g_norm + w_pos * p_norm

    Los pesos deben sumar 1 (se renormalizan internamente si no lo hacen).
    Los componentes f_norm, g_norm, p_norm están normalizados a [0, 1].
    """
    # Normalización min-max sobre los valores de la ventana
    # Frecuencia: cuántas veces apareció / máximo posible en la ventana
    max_possible = freq_window  # en window sorteos, cada número aparece como mucho window veces
    f_norm = freq / max_possible if max_possible > 0 else 0.0

    # Atraso: cuanto más tiempo lleva sin salir, "mayor" el score (si queremos vencidos)
    # Normalizamos sobre el window: gap/window ∈ [0,1], pero queremos que MAYOR atraso = MAYOR score
    # así que usamos 1 - gap/window invertido... en realidad definimos g_norm = gap/window
    # y dejamos que el usuario decida el signo. Pondremos g_norm = gap / gap_window.
    g_norm = gap / gap_window if gap_window > 0 else 0.0

    # Posicional: qué tan cerca está el número de su posición teórica esperada.
    # Si pos_idx es None (posición no disponible), p_norm = 0.5 (neutral).
    if pos_idx is not None:
        # La teoría dice: posición esperada del número n es ~1 + 19*(n-1)/79.
        # El pos_idx que pasamos ya es la distancia o acuerdo... lo trataremos como:
        # qué tan "promedio" está el número en su posición. Usaremos 1 - |desviación| para que
        # valores cercanos a la posición teórica den score alto.
        # Aquí asumeremos que el caller ya calculó algún medida de acuerdo; si no, 0.5.
        p_norm = 0.5  # placeholder: la UI pasará un valor calculado
    else:
        p_norm = 0.5

    # Renormalizar pesos si no suman 1
    total = w_freq + w_gap + w_pos
    w_freq_n = w_freq / total if total > 0 else w_freq
    w_gap_n = w_gap / total if total > 0 else w_gap
    w_pos_n = w_pos / total if total > 0 else w_pos

    score = w_freq_n * f_norm + w_gap_n * g_norm + w_pos_n * p_norm
    return float(score)


# ── Afinidad de conjuntos (lift de pares) ───────────────────────────────

def set_affinity_mean_lift(pair_lift: np.ndarray, subset: Tuple[int, ...]) -> float:
    """Promedio del lift de todos los pares de un subconjunto de números.

    pair_lift: matriz 80×80 (symmetrical, diagonal 1).
    subset: tupla de números (ej. (5, 12, 23, ...)).
    """
    if len(subset) < 2:
        return 1.0
    total = 0.0
    count = 0
    for i in range(len(subset)):
        for j in range(i + 1, len(subset)):
            a, b = subset[i], subset[j]
            total += pair_lift[a - 1, b - 1]  # 0-indexed internally
            count += 1
    return total / count if count > 0 else 1.0


# ── Generación de combinaciones con temperatura ──────────────────────────

def softmax_weights(scores: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Convertir scores a probabilidades vía softmax con temperatura T.

    T bajo → distribución concentrada en los de mayor score.
    T alto → distribución más uniforme (mayor diversidad).
    """
    scores = np.asarray(scores, dtype=float)
    # Para estabilidad numérica restamos el máximo
    shifted = scores - scores.max()
    exp_vals = np.exp(shifted / temperature)
    probs = exp_vals / exp_vals.sum()
    return probs


def generate_ticket(
    scores: np.ndarray,
    temperature: float = 1.0,
    rng: np.random.Generator = None,
) -> Tuple[Tuple[int, ...], float]:
    """Generar un boleto de 10 números únicos usando muestreo ponderado.

    Retorna (boleto, score_total) donde boleto es una tupla de 10 números
    ordenados y score_total es la suma de scores individuales más la afinidad.
    """
    if rng is None:
        rng = np.random.default_rng()

    # Pesos por softmax
    probs = softmax_weights(scores, temperature=temperature)

    # Muestreo sin reemplazo de 10 números
    # numpy's choice con replace=False y probabilidades
    indices = rng.choice(80, size=10, replace=False, p=probs)
    numbers = tuple(sorted(int(i + 1) for i in indices))

    # Score total = suma de scores individuales + λ * afinidad media de pares
    # λ (lambda) weight for affinity
    LAMBDA = 0.1

    # Calcular score individual sumado
    score_sum = float(sum(scores[n - 1] for n in numbers))

    # Afinidad simple: promedio de lifts de pares (usaremos 1.0 por defecto si no hay matrix)
    affinity_mean = 1.0

    score_total = score_sum + LAMBDA * affinity_mean

    return numbers, score_total


def generate_combinations(
    scores: np.ndarray,
    temperature: float = 1.0,
    n_combinations: int = 10,
    rng_seed: Optional[int] = None,
    /,
) -> List[Tuple[Tuple[int, ...], float]]:
    """Generar N combinaciones distintas de 10 números.

    Retorna lista de ((números ordenados), score_total) de tamaño n_combinations.
    Usa temperatura y semilla para reproducibilidad.
    """
    if rng_seed is not None:
        rng = np.random.default_rng(rng_seed)
    else:
        rng = np.random.default_rng()

    combinations: List[Tuple[Tuple[int, ...], float]] = []
    seen: set = set()  # para asegurar unicidad (tuplas ordenadas)

    # Pre-computar el mean lift para acelerar (usaremos 1.0 placeholder; la UI pasará la matrix)
    # Para simplicidad, calculamos score_simple = suma de scores individuales

    for _ in range(n_combinations * 2):  # over-generate to handle rare collisions
        numbers, score_total = generate_ticket(scores, temperature=temperature, rng=rng)
        key = numbers  # ya es tuple ordenado
        if key not in seen:
            seen.add(key)
            combinations.append((numbers, score_total))
            if len(combinations) >= n_combinations:
                break

    # Si no logramos N únicas, rellenar con las que tengamos
    while len(combinations) < n_combinations:
        # generar uno más simple: los 10 de mayor score (determinista)
        top_indices = np.argsort(scores)[-10:][::-1]  # mayores scores primero
        det_numbers = tuple(sorted(int(i + 1) for i in top_indices))
        key = det_numbers
        if key not in seen:
            seen.add(key)
            # score_simple = suma de los 10 scores más altos
            score_sum = float(sum(scores[j] for j in top_indices))
            combinations.append((det_numbers, score_sum))
        if len(combinations) >= n_combinations:
            break

    return combinations


# ── Explicabilidad de un boleto ─────────────────────────────────────────

def ticket_explainer(
    numbers: Tuple[int, ...],
    scores: np.ndarray,
    /,
    *,
    include_posicional: bool = True,
) -> dict:
    """Devolver un dict descriptivo de por qué se eligieron estos 10 números.

    Incluye: score total, desglose por componente, posición teórica.
    """
    score_sum = float(sum(scores[n - 1] for n in numbers))

    parts: List[dict] = []
    for n in numbers:
        parts.append({
            "number": n,
            "score": float(scores[n - 1]),
            "position_theoretical": 1 + 19 * (n - 1) / 79,
        })

    return {
        "numbers": list(numbers),
        "score_total": score_sum,
        "component_breakdown": parts,
        "include_posicional": include_posicional,
    }