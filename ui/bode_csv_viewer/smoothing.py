"""
Lissage des courbes pour le viewer Bode CSV. Autonome.
Moyenne glissante et Savitzky-Golay (si scipy disponible).
"""
from typing import List

try:
    from scipy.signal import savgol_filter
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False
    savgol_filter = None


def has_savgol() -> bool:
    """True si le lissage Savitzky-Golay est disponible (scipy)."""
    return _HAS_SCIPY


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


def smooth_savgol(values: List[float], window_length: int, polyorder: int = 2) -> List[float]:
    """
    Lissage Savitzky-Golay (préserve mieux les pics). Nécessite scipy.
    window_length impair (3 à 11), polyorder < window_length.
    """
    if not _HAS_SCIPY or len(values) < window_length:
        return list(values)
    w = min(max(3, window_length | 1), len(values) | 1)  # impair
    p = min(polyorder, w - 1)
    return list(savgol_filter(values, w, p))
