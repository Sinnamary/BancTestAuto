"""
Affichage de la ligne horizontale à -3 dB. Autonome viewer CSV.
Convient à tous les types de filtres (passe-bas, coupe-bande, etc.).
"""
from typing import Any, Optional

import pyqtgraph as pg
from PyQt6.QtCore import Qt

# Niveau -3 dB en gain linéaire (Us/Ue)
LEVEL_DB = -3.0
LEVEL_LINEAR = 10 ** (LEVEL_DB / 20.0)


class CutoffMarkerViz:
    """Ligne horizontale rouge à -3 dB (gain) avec étiquette."""
    PEN = pg.mkPen("#ff6060", width=2.5, style=Qt.PenStyle.DashLine)
    Z_LINE = 10
    Z_LABEL = 11

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._line: Optional[Any] = None
        self._label: Optional[Any] = None
        self._y_level: Optional[float] = None

    def set_level(self, y_value: Optional[float]) -> None:
        """
        Affiche une ligne horizontale au niveau gain donné.
        y_value: en dB (-3) ou en linéaire (Us/Ue) selon l'axe Y. None = masquer.
        """
        self._y_level = y_value
        if self._line is None:
            self._line = pg.InfiniteLine(
                pos=LEVEL_DB, angle=0, movable=False, pen=self.PEN,
            )
            self._line.setZValue(self.Z_LINE)
            self._plot_item.addItem(self._line)
        if self._label is None:
            self._label = pg.TextItem(anchor=(1, 0.5), text="-3 dB")
            self._label.setColor("#ff5050")
            self._label.setZValue(self.Z_LABEL)
            self._plot_item.addItem(self._label)
        if y_value is not None:
            self._line.setPos(y_value)
            self._line.setVisible(True)
            self._label.setVisible(True)
            self.update_label_position()
        else:
            self._line.setVisible(False)
            self._label.setVisible(False)

    def update_label_position(self) -> None:
        if self._y_level is None or self._label is None or not self._label.isVisible():
            return
        vb = self._plot_item.getViewBox()
        if vb:
            x_min, x_max = vb.viewRange()[0]
            self._label.setPos(x_max, self._y_level)
