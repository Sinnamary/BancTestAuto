"""
Contrôle du quadrillage du graphique Bode CSV. Isolé du reste de l'app.
"""
from typing import Any


class BodePlotGrid:
    """Gère l'affichage du quadrillage sur un PlotItem pyqtgraph."""
    ALPHA_DARK = 0.35   # fond noir
    ALPHA_LIGHT = 0.55  # fond blanc : plus marqué pour bonne lisibilité

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._visible = True
        self._dark_background = True
        self._apply()

    def set_visible(self, visible: bool) -> None:
        self._visible = bool(visible)
        self._apply()

    def set_dark_background(self, dark: bool) -> None:
        """True = fond noir, False = fond blanc (alpha du quadrillage adapté)."""
        self._dark_background = dark
        self._apply()

    def is_visible(self) -> bool:
        return self._visible

    def _apply(self) -> None:
        alpha = self.ALPHA_DARK if self._dark_background else self.ALPHA_LIGHT
        self._plot_item.showGrid(x=self._visible, y=self._visible, alpha=alpha)
