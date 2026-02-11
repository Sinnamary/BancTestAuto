"""
État d'affichage du viewer Bode CSV. Objet valeur, sans lien avec le reste de l'app.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class BodeViewOptions:
    """Options d'affichage du graphique (quadrillage, lissage, fond, couleur courbe, etc.).
    Par défaut : fond noir (plot_background_dark=True)."""
    grid_visible: bool = True
    smooth_window: int = 0
    show_raw_curve: bool = False
    y_linear: bool = False
    plot_background_dark: bool = True  # fond noir par défaut ; False = fond blanc
    curve_color: str = "#e0c040"  # couleur courbe principale (hex)

    SMOOTH_WINDOW_CHOICES: List[int] = (3, 5, 7, 9, 11)
    SMOOTH_METHODS: List[tuple] = (
        ("Moyenne glissante", False),
        ("Savitzky-Golay", True),
    )
    BACKGROUND_CHOICES: List[tuple] = (("Noir", True), ("Blanc", False))
    CURVE_COLOR_CHOICES: List[tuple] = (
        ("Jaune", "#e0c040"),
        ("Rouge", "#e04040"),
        ("Vert", "#40c040"),
        ("Bleu", "#4080e0"),
        ("Cyan", "#40c0c0"),
        ("Magenta", "#c040c0"),
        ("Orange", "#e09030"),
        ("Blanc", "#ffffff"),
    )

    @classmethod
    def default(cls) -> "BodeViewOptions":
        return cls()
