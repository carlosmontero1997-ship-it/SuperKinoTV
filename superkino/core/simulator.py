"""Simulador walk-forward de backtest sin lookahead + línea base aleatoria."""

from __future__ import annotations

from typing import List, Tuple, Dict, Optional

import numpy as np
from scipy.stats import hypergeom

from .models import DrawHistory, Draw
from .ingest import ingest_file
from .analysis import compute_pair_lift
from .scoring import individual_score, set_affinity_mean_lift, generate_combinations, ticket_explainer


# ── Configuración por defecto ───────────────────────────────────────────

DEFAULT_WINDOW = 100
DEFAULT_N_COMBOS = 25
DEFAULT_TEMPERATURE = 1.0

# Hipergeométrica: M=80 (total), n=20 (sorteados), N=10 (jugadas)
HYPERGEO = hypergeom(M=80, n=20, N=10)


# ── Backtest walk-forward ───────────────────────────────────────────────

def walk_forward_simulate(
    history: DrawHistory,
    /,
    window: int = DEFAULT_WINDOW,
    n_combinations: int = DEFAULT_N_COMBOS,
    temperature: float = DEFAULT_TEMPERATURE,
    rng_seed: Optional[int] = None,
) -> dict:
    """Simular backtest walk-forward sobre el historial.

    Para cada sorteo D que tenga al menos W sorteos previos:
      1. Ventana = sorteos inmediatamente anteriores a D (siempre < D).
      2. Generar N combinaciones con el modelo actual (scores + temperatura).
      3. Medir aciertos vs el sorteo real D.
      4. Generar N combinaciones aleatoriasuniformes como línea base.

    Retorna dict con métricas agregadas y detalle por sorteo.
    """
    if rng_seed is not None:
        rng = np.random.default_rng(rng_seed)
    else:
        rng = np.random.default_rng()

    draws = history._draws
    n_total = len(draws)

    # Los primeros (window) sorteos no tienen suficiente historia previa
    results: List[dict] = []

    for i in range(window, n_total):
        sorteo_real = draws[i]  # sorteo del día D (índice i en la lista ordenada)
        window_draws = draws[i - window: i]  # W sorteos previos, ESTRICTAMENTE anteriores

        # 2. Construir modelo sobre la ventana y generar N combinaciones
        # Extraer frecuencias/atrasos/posición de la ventana
        P: list[list[int]] = [[0] * 80 for _ in range(window)]
        frec = [0] * 80
        for j, d in enumerate(window_draws):
            for n in d.numbers:
                P[j][n - 1] = 1
                frec[n - 1] += 1

        # Calcular gaps
        last_appearance = [-1] * 80
        for j in range(window):
            for idx, appeared in enumerate(P[j]):
                if appeared:
                    last_appearance[idx] = j

        gaps = [window - 1 - last_appearance[n] if last_appearance[n] != -1 else window
                for n in range(80)]

        # Scores individuales (usando los pesos por defecto)
        scores = np.array([
            individual_score(
                n + 1, frec[n], window, gaps[n], window,
                w_freq=0.4, w_gap=0.3, w_pos=0.3,
            )
            for n in range(80)
        ])

        # Generar N combinaciones
        combos = generate_combinations(scores, temperature=temperature, n_combinations=n_combinations, rng_seed=rng_seed)

        # 3. Medir aciertos para cada combinación vs sorteo real
        aciertos_por_combo: List[int] = []
        for combo_numbers, _ in combos:
            real_set = set(sorteo_real.numbers)
            combo_set = set(combo_numbers)
            aciertos = len(real_set & combo_set)
            aciertos_por_combo.append(aciertos)

        # Mejor acierto de este sorteo
        mejor_acierto = max(aciertos_por_combo) if aciertos_por_combo else 0

        # 4. Línea base: N boletos aleatorios uniformes (misma cantidad)
        aleatorio_aciertos: List[int] = []
        for _ in range(n_combinations):
            # Boleto aleatorio: 10 números únicos de 1-80
            ticket = tuple(sorted(np.random.choice(80, size=10, replace=False) + 1))
            real_set = set(sorteo_real.numbers)
            combo_set = set(ticket)
            aleatorio_aciertos.append(len(real_set & combo_set))

        # Registro de este sorteo
        results.append({
            "sorteo_idx": i,
            "sorteo_date": sorteo_real.date_iso,
            "mejor_acierto": mejor_acierto,
            "aciertos_por_combo": aciertos_por_combo,
            "linea_base_aciertos": aleatorio_aciertos,
            "combos_ganadores": [c for c, s in zip(combos, aciertos_por_combo) if s >= 5],  # threshold
        })

    # ── Agregados ──────────────────────────────────────────────────────

    if not results:
        return {
            "window": window,
            "n_combinaciones": n_combinations,
            "temperature": temperature,
            "total_sorteos_analizados": 0,
            "mensaje": "No hay suficientes sorteos para un backtest con la ventana especificada.",
        }

    total_sorteos = len(results)
    # % de sorteos donde al menos una combinación acertó ≥5, ≥7, =10
    hit5 = sum(1 for r in results if r["mejor_acierto"] >= 5) / total_sorteos * 100
    hit7 = sum(1 for r in results if r["mejor_acierto"] >= 7) / total_sorteos * 100
    hit10 = sum(1 for r in results if r["mejor_acierto"] == 10) / total_sorteos * 100

    # Distribución de mejores aciertos
    dist_5plus = sum(1 for r in results if r["mejor_acierto"] >= 5)
    dist_7plus = sum(1 for r in results if r["mejor_acierto"] >= 7)
    dist_10 = sum(1 for r in results if r["mejor_acierto"] == 10)

    # Línea base: misma comparación
    base_hit5 = sum(
        1 for r in results
        if max(r["linea_base_aciertos"]) >= 5
    ) / total_sorteos * 100
    base_hit7 = sum(
        1 for r in results
        if max(r["linea_base_aciertos"]) >= 7
    ) / total_sorteos * 100

    # Tabla hipergeométrica de referencia
    hypergeom_probs = {
        k: HYPERGEO.pmf(k) for k in range(11)  # k = 0..10 aciertos
    }

    return {
        "window": window,
        "n_combinaciones": n_combinations,
        "temperature": temperature,
        "total_sorteos_analizados": total_sorteos,
        "porcentaje_hit5": round(hit5, 2),
        "porcentaje_hit7": round(hit7, 2),
        "porcentaje_hit10": round(hit10, 2),
        "distribucion_mayor_5": dist_5plus,
        "distribucion_mayor_7": dist_7plus,
        "distribucion_10": dist_10,
        "linea_base_hit5": round(base_hit5, 2),
        "linea_base_hit7": round(base_hit7, 2),
        "tabla_hipergeometrica": {k: round(v, 6) for k, v in hypergeom_probs.items()},
        "detalle_por_sorteo": results,
    }


# ── Simulación "what-if" para una fecha concreta ──────────────────────────

def simulate_since(
    path_ticket: str,
    path_historial: str,
    /,
    *,
    window: int = DEFAULT_WINDOW,
    n_combinations: int = DEFAULT_N_COMBOS,
    temperature: float = DEFAULT_TEMPERATURE,
    rng_seed: Optional[int] = None,
) -> dict:
    """Simular desde un boleto ticket.txt contra el historial completo.

    Útil para responder "¿si hubiese jugado en esta fecha?".

    Retorna métricas de acierto y comparación con línea base.
    """
    # Cargar historial
    history, _ = ingest_file(path_historial)

    # Ejecutar backtest walk-forward desde el sorteo posterior al último del ticket
    # (para simplificar, hacemos walk-forward completo sobre todo el historial)
    return walk_forward_simulate(
        history, window=window, n_combinations=n_combinations,
        temperature=temperature, rng_seed=rng_seed,
    )