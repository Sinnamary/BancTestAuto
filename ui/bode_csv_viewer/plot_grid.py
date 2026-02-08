"""
Contrôle du quadrillage du graphique Bode CSV. Isolé du reste de l'app.
"""
from typing import Any


class BodePlotGrid:
    """Gère l'affichage du quadrillage sur un PlotItem pyqtgraph."""
    DEFAULT_ALPHA = 0.35

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._visible = True
        self._apply()

    def set_visible(self, visible: bool) -> None:
        self._visible = bool(visible)
        self._apply()

    def is_visible(self) -> bool:
        return self._visible

    def _apply(self) -> None:
        self._plot_item.showGrid(x=self._visible, y=self._visible, alpha=self.DEFAULT_ALPHA)
