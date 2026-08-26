"""Ingesta y validación de sorteos — operaciones puras, sin importar streamlit."""

from __future__ import annotations

import re
from typing import List, Tuple

from .models import Draw, DrawHistory, parse_line


# ── Expresión regular para validar la estructura de una línea ──────────

# Formato esperado: DD/MM/AAAA,n1,n2,...,n20
# Cada número debe ser entero de 1-80 y únicos dentro de la línea.
LINE_PATTERN = re.compile(
    r"^(\d{2})/(\d{2})/(\d{4}),"  # fecha DD/MM/AAAA
    r"(\d{1,2})(,(\d{1,2})){19}$"  # 20 números enteros separadores por coma
)


def validate_line_structure(raw: str) -> Tuple[bool, str | None]:
    """Devolver (ok, motivo_error). OK si la línea cumple el patrón estructural básico."""
    m = LINE_PATTERN.match(raw.strip())
    if not m:
        return False, "formato inválido: se espera DD/MM/AAAA,n1,n2,...,n20 con 20 números"
    return True, None


def parse_and_validate_line(raw: str) -> Tuple[bool, Draw | None, str | None]:
    """Parsear y validar completamente una línea.

    Devuelve (ok, draw, motivo_error).
    Si ok es False, draw es None y motivo_error explica por qué.
    """
    # 1. Patrón estructural
    ok, err = validate_line_structure(raw)
    if not ok:
        return False, None, err

    # 2. Parseo básico (intenta crear Draw; esto cubre rangos, unicidad, etc.)
    draw = parse_line(raw)
    if draw is None:
        return False, None, "no se pudo parsear la línea (revisa rango 1-80 y unicidad)"

    return True, draw, None


def ingest_lines(
    lines: List[str], /, *,
    reject_duplicates: bool = True,
) -> tuple[DrawHistory, list[tuple[int, str]]]:
    """Parsear e validar múltiples líneas en un DrawHistory.

    Devuelve (history, problemas) donde problemas es una lista de
    (línea_idx, motivo) para aquellas líneas que no pasaron la validación.
    """
    # Filtrar líneas vacías y validar estructura antes de crear DrawHistory
    valid_lines: List[str] = []
    problemas: list[tuple[int, str]] = []

    for idx, raw in enumerate(lines):
        ok, draw, err = parse_and_validate_line(raw)
        if not ok:
            problemas.append((idx, err))
        else:
            valid_lines.append(raw.strip())

    # Usar el factory del historial (que también chequea duplicados por fecha)
    history, extra_problems = DrawHistory.from_validated_lines(
        valid_lines, reject_duplicates=reject_duplicates,
    )
    problemas.extend(extra_problems)

    return history, problemas


def ingest_file(path: str, /, *, reject_duplicates: bool = True) -> tuple[DrawHistory, list[tuple[int, str]]]:
    """Cargar y validar un archivo de sorteos.

    Retorna (history, problemas). Los problemas incluyen formato inválido,
    números fuera de rango, duplicados y huecos de fechas.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return ingest_lines(lines, reject_duplicates=reject_duplicates)


# ── Funciones de utilidad para el análisis ---------------------------

def compute_presence_matrix(history: DrawHistory, window: int = 100) -> Tuple[list[list[int]], list[int]]:
    """Matriz de presencia W×80 y frecuencias.

    Retorna (P, frec) donde P[i][n-1] = 1 si el número n apareció en el sorteo i
    de la ventana (últimos 'window' sorteos), y frec[n-1] = conteo total.
    """
    draws = history._draws[-window:]  # últimos W sorteos
    P: list[list[int]] = [[0] * 80 for _ in range(len(draws))]
    frec = [0] * 80

    for i, draw in enumerate(draws):
        for n in draw.numbers:
            col = n - 1  # índice 0-based
            P[i][col] = 1
            frec[col] += 1

    return P, frec


def compute_gaps(presence_matrix: list[list[int]], window: int) -> list[int]:
    """Atraso (sorteos desde última aparición) por cada número.

    Si un número nunca apareció en la ventana, su atraso = window.
    """
    n_numbers = 80
    gaps = [window] * n_numbers  # default: nunca apareció

    # Recorrer la matriz de abajo hacia arriba (últimos sorteos primero)
    for i in range(len(presence_matrix) - 1, -1, -1):
        row = presence_matrix[i]
        for n in range(n_numbers):
            if row[n] == 1:
                # Este número apareció en el sorteo i;
                # su atraso actual es el número de sorteos desde este hasta el siguiente appearance
                # Como recorremos de abajo hacia arriba, el primer hit es el más reciente
                # Pero necesitamos contar desde la última aparición anterior...
                pass

    # Algoritmo más simple: para cada número, contar ceros consecutivos al final
    # y desde cualquier zero en medio.
    # Re-implementación clara:
    last_appearance = [-1] * n_numbers  # índice del último sorteo donde apareció (-1 = nunca)
    for i in range(len(presence_matrix)):
        for n in range(n_numbers):
            if presence_matrix[i][n] == 1:
                last_appearance[n] = i

    for n in range(n_numbers):
        if last_appearance[n] == -1:
            gaps[n] = window  # nunca apareció
        else:
            gaps[n] = len(presence_matrix) - 1 - last_appearance[n]

    return gaps


def compute_positional_stats(history: DrawHistory, window: int = 100) -> dict:
    """Estadísticas posicionales: distribuciones empíricas vs teóricas.

    Retorna un dict con:
    - empirical: lista de length window, cada elemento es una lista de 20 ints (los números ordenados)
    - empirical_means: lista length 20, media de cada posición
    - theoretical_means: lista length 20, j*81/21 para j=1..20
    - per_number_theoretical: dict number->teoría posición esperada
    """
    draws = history._draws[-window:]
    n = len(draws)

    # Empírico: números por posición
    emp_means = [0.0] * 20
    for draw in draws:
        for pos in range(20):
            emp_means[pos] += draw.numbers[pos]
    emp_means = [m / n for m in emp_means]

    # Teórico: j * 81 / 21 para j = 1..20
    theor_means = [j * 81 / 21 for j in range(1, 21)]

    # Posición teórica esperada para cada número n:
    # 1 + 19*(n-1)/79
    per_number_theory: dict[int, float] = {}
    for n in range(1, 81):
        per_number_theory[n] = 1 + 19 * (n - 1) / 79

    return {
        "n": n,
        "empirical_means": emp_means,
        "theoretical_means": theor_means,
        "per_number_theoretical": per_number_theory,
    }


def compute_pair_lift(presence_matrix: list[list[int]], window: int) -> Tuple[list[list[int]], list[list[float]]]:
    """Lift de co-ocurrencia de pares.

    Retorna (observed, lift) matrices 80×80.
    observed[i][j] = veces que i y j salieron juntos en la ventana.
    lift[i][j] = observed / expected, donde expected = window * (20/80) * (19/79).
    """
    n_numbers = 80
    expected = window * (20 / 80) * (19 / 79)  # ≈ window * 0.06013

    # observed = PᵀP - diag (quitar auto-ocurrencia)
    observed = [[0] * n_numbers for _ in range(n_numbers)]
    for i in range(window):
        row_i = presence_matrix[i]
        for n in range(n_numbers):
            if row_i[n]:
                for m in range(n + 1, n_numbers):
                    if row_i[m]:
                        observed[n][m] += 1
                        observed[m][n] += 1

    # Lift
    lift = [[1.0] * n_numbers for _ in range(n_numbers)]  # diagonal = 1
    for i in range(n_numbers):
        for j in range(n_numbers):
            if i != j:
                obs = observed[i][j]
                lift[i][j] = obs / expected if expected > 0 else 0.0

    return observed, lift


def compute_sums_parity_decades(history: DrawHistory, window: int = 100) -> dict:
    """Suma total, impares/pares, y distribución por decena por sorteo de la ventana."""
    draws = history._draws[-window:]
    sums = []
    parity_counts = []  # (impares, pares) por sorteo
    decade_counts = []  # lista de 8 ints (cantidad por decena 1-10, 11-20, ..., 71-80)

    for draw in draws:
        nums = draw.numbers
        s = sum(nums)
        sums.append(s)
        impares = sum(1 for n in nums if n % 2 == 1)
        pares = 20 - impares
        parity_counts.append((impares, pares))

        decadas = [0] * 8
        for n in nums:
            # decena: (n-1)//10 da 0 para 1-10, 1 para 11-20, ..., 7 para 71-80
            decadas[(n - 1) // 10] += 1
        decade_counts.append(decadas)

    return {
        "sums": sums,
        "parity_counts": parity_counts,
        "decade_counts": decade_counts,
        "sum_avg": sum(sums) / len(sums) if sums else 0,
    }