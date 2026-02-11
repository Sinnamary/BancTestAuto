"""
Modèle de données propre au visualiseur Bode CSV. Aucune dépendance au reste de l'app.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BodeCsvPoint:
    """Un point de mesure Bode (fréquence, gain). Utilisé uniquement par le viewer CSV."""
    f_hz: float
    us_v: float
    gain_linear: float
    gain_db: float
    ue_v: Optional[float] = None  # Optionnel (acquisition oscilloscope)
    phase_deg: Optional[float] = None  # Optionnel (acquisition oscilloscope, Phase 5)


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

    def has_phase(self) -> bool:
        """True si au moins un point a une phase (acquisition oscilloscope)."""
        return any(getattr(p, "phase_deg", None) is not None for p in self._points)

    def phases_deg(self) -> List[Optional[float]]:
        """Liste des phases en degrés (None si non mesuré). Pour usage Phase 5."""
        return [getattr(p, "phase_deg", None) for p in self._points]

    def is_empty(self) -> bool:
        return len(self._points) == 0
