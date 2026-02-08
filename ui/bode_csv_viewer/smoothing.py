"""
Lissage des courbes pour le viewer Bode CSV. Autonome.
"""
from typing import List


class MovingAverageSmoother:
    """Moyenne glissante centrée (fenêtre 3 à 11 points)."""
    MIN_WINDOW = 1
    MAX_WINDOW = 11

    def __init__(self, window: int = 5):
        self._window = max(self.MIN_WINDOW, min(self.MAX_WINDOW, window))

    @property
    def window(self) -> int:
        return self._window

    def set_window(self, window: int) -> None:
        self._window = max(self.MIN_WINDOW, min(self.MAX_WINDOW, window))

    def smooth(self, values: List[float]) -> List[float]:
        n = len(values)
        if n == 0 or self._window <= 1:
            return list(values)
        w = min(self._window, n)
        half = w // 2
        result: List[float] = []
        for i in range(n):
            start = max(0, i - half)
            end = min(n, i + half + 1)
            result.append(sum(values[start:end]) / (end - start))
        return result
