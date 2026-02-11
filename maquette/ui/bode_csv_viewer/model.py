"""
Modèle de données propre au visualiseur Bode CSV. Aucune dépendance au reste de l'app.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class BodeCsvPoint:
    """Un point de mesure Bode (fréquence, gain). Utilisé uniquement par le viewer CSV."""
    f_hz: float
    us_v: float
    gain_linear: float
    gain_db: float


class BodeCsvDataset:
    """Conteneur de points Bode chargés depuis un CSV. Calculs dérivés locaux."""
    __slots__ = ("_points",)

    def __init__(self, points: List[BodeCsvPoint]):
        self._points = list(points)

    @property
    def points(self) -> List[BodeCsvPoint]:
        return self._points

    @property
    def count(self) -> int:
        return len(self._points)

    def freqs_hz(self) -> List[float]:
        return [p.f_hz for p in self._points]

    def gains_db(self) -> List[float]:
        return [p.gain_db for p in self._points]

    def gains_linear(self) -> List[float]:
        return [p.gain_linear for p in self._points]

    def is_empty(self) -> bool:
        return len(self._points) == 0
