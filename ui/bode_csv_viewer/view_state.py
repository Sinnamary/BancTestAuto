"""
État d'affichage du viewer Bode CSV. Objet valeur, sans lien avec le reste de l'app.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class BodeViewOptions:
    """Options d'affichage du graphique (quadrillage, lissage, etc.)."""
    grid_visible: bool = True
    smooth_window: int = 0
    show_raw_curve: bool = False
    show_cutoff: bool = True
    y_linear: bool = False

    SMOOTH_WINDOW_CHOICES: List[int] = (3, 5, 7, 9, 11)

    @classmethod
    def default(cls) -> "BodeViewOptions":
        return cls()
