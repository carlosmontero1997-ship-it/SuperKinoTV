"""Modelos de dominio puros — sin importar streamlit ni la UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class Draw:
    """Un sorteo individual: fecha ISO y los 20 números ordenados."""

    date_iso: str  # 'YYYY-MM-DD'
    numbers: tuple[int, ...]  # exactamente 20 números únicos, 1-80, orden ascendente

    def __post_init__(self) -> None:
        if len(self.numbers) != 20:
            raise ValueError("Un sorteo debe tener exactamente 20 números.")
        if not all(1 <= n <= 80 for n in self.numbers):
            raise ValueError("Los números deben estar en el rango 1-80.")
        if len(set(self.numbers)) != 20:
            raise ValueError("Los números deben ser únicos dentro de un sorteo.")


class DrawHistory:
    """Historial ordenado por fecha, con validación y utilidades de análisis."""

    def __init__(self, draws: Optional[List[Draw]] = None) -> None:
        self._draws: List[Draw] = draws if draws is not None else []
        # Índice por fecha para búsquedas O(1)
        self._by_date: Dict[str, Draw] = {d.date_iso: d for d in self._draws}
        # Ordenado cronológico (ya lo está por inserción ordenada)
        self._sorted: bool = self._check_sorted()

    def _check_sorted(self) -> bool:
        return all(
            self._draws[i].date_iso <= self._draws[i + 1].date_iso
            for i in range(len(self._draws) - 1)
        )

    # ---- Propiedades públicas ----

    @property
    def count(self) -> int:
        return len(self._draws)

    @property
    def dates(self) -> List[str]:
        return [d.date_iso for d in self._draws]

    def get(self, date_iso: str) -> Optional[Draw]:
        return self._by_date.get(date_iso)

    def __getitem__(self, idx: int) -> Draw:
        return self._draws[idx]

    def __len__(self) -> int:
        return len(self._draws)

    def __repr__(self) -> str:
        return f"DrawHistory(n={len(self)})"

    # ---- Factories ----

    @classmethod
    def from_validated_lines(
        cls, lines: List[str], /, *,
        reject_duplicates: bool = True,
    ) -> tuple["DrawHistory", list[tuple[int, str]]]:
        """Parsear líneas 'DD/MM/AAAA,n1,...,n20' y devolver (history, problemas).

        Cada problema es (línea_idx, motivo).
        """
        history = cls()
        problemas: list[tuple[int, str]] = []

        for idx, raw in enumerate(lines):
            raw = raw.strip()
            if not raw:
                continue

            parts = raw.split(",")
            if len(parts) != 21:
                problemas.append((idx, "formato: se esperan 1 fecha + 20 números"))
                continue

            date_str = parts[0].strip()
            num_strs = parts[1:]

            # Validación de fecha (formato DD/MM/AAAA, día primero)
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                date_iso = dt.strftime("%Y-%m-%d")
            except ValueError:
                problemas.append((idx, f"fecha inválida: '{date_str}'"))
                continue

            # Validación y conversión de números
            try:
                nums = [int(s.strip()) for s in num_strs]
            except ValueError:
                problemas.append((idx, "todos los valores deben ser enteros"))
                continue

            # Rango 1-80
            if not all(1 <= n <= 80 for n in nums):
                problemas.append((idx, "los números deben estar en el rango 1-80"))
                continue

            # Unicidad dentro de la línea
            if len(set(nums)) != 20:
                problemas.append((idx, "los números deben ser únicos dentro del sorteo"))
                continue

            # Construir Draw y agregar
            try:
                draw = Draw(date_iso=date_iso, numbers=tuple(sorted(nums)))
            except ValueError as e:
                problemas.append((idx, str(e)))
                continue

            # Verificar duplicado por fecha
            if reject_duplicates and date_iso in history._by_date:
                problemas.append((idx, f"fecha duplicada: {date_iso}"))
                continue

            history._draws.append(draw)
            history._by_date[date_iso] = draw

        # Re-ordenar después de la inserción para mantener sorted
        history._draws.sort(key=lambda d: d.date_iso)
        history._by_date = {d.date_iso: d for d in history._draws}
        history._sorted = history._check_sorted()

        return history, problemas

    @classmethod
    def from_file_path(cls, path: str, /, *, reject_duplicates: bool = True) -> tuple["DrawHistory", list[tuple[int, str]]]:
        """Cargar y validar un archivo de texto con un sorteo por línea."""
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return cls.from_validated_lines(lines, reject_duplicates=reject_duplicates)

    def to_file_path(self, path: str) -> None:
        """Escribir el historial de vuelta al mismo formato de entrada."""
        lines = []
        for d in self._draws:
            nums_str = ",".join(str(n) for n in d.numbers)
            lines.append(f"{d.date_iso},{nums_str}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


# ── FUNCIONES AUXILIARES DE ANÁLISIS ────────────────────────────────

def detect_gaps(dates: List[str], /, min_date: Optional[str] = None, max_date: Optional[str] = None) -> List[str]:
    """Dado una lista de fechas ISO, devolver las fechas faltantes en el rango.

    Las fechas se esperan en formato 'YYYY-MM-DD' y deben estar ordenadas.
    Si min_date/max_date son None, se usan los extremos de la lista.
    """
    from datetime import datetime, timedelta

    if not dates:
        return []

    all_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    min_d = min_date if min_date else min(all_dates)
    max_d = max_date if max_date else max(all_dates)

    present = {datetime.strptime(d, "%Y-%m-%d") for d in all_dates}
    missing: List[str] = []

    current = min_d
    while current <= max_d:
        if current not in present:
            missing.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return missing


def parse_line(line: str) -> Optional[Draw]:
    """Parsear una sola línea; devuelve Draw si es válido, None en caso contrario."""
    try:
        hist, _ = DrawHistory.from_validated_lines([line])
        return hist[0] if hist.count > 0 else None
    except Exception:
        return None