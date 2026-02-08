"""
Contrôle du quadrillage du graphique Bode CSV. Isolé du reste de l'app.
Quadrillage majeur (showGrid) + optionnel mineur (lignes intermédiaires en log).
"""
import math
from typing import Any, List

import pyqtgraph as pg
from PyQt6.QtCore import Qt


class BodePlotGrid:
    """Gère l'affichage du quadrillage (majeur + mineur) sur un PlotItem pyqtgraph."""
    ALPHA_DARK = 0.35   # fond noir
    ALPHA_LIGHT = 0.55  # fond blanc : plus marqué pour bonne lisibilité
    ALPHA_MINOR = 0.18  # quadrillage mineur plus discret

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._visible = True
        self._minor_visible = False
        self._dark_background = True
        self._minor_lines: List[Any] = []
        self._apply()
        vb = plot_item.getViewBox()
        if vb:
            vb.sigRangeChanged.connect(self._on_range_changed)

    def set_visible(self, visible: bool) -> None:
        self._visible = bool(visible)
        self._apply()

    def set_minor_visible(self, visible: bool) -> None:
        self._minor_visible = bool(visible)
        self._clear_minor()
        if self._minor_visible:
            self._update_minor_lines()

    def set_dark_background(self, dark: bool) -> None:
        self._dark_background = dark
        self._apply()

    def is_visible(self) -> bool:
        return self._visible

    def _apply(self) -> None:
        alpha = self.ALPHA_DARK if self._dark_background else self.ALPHA_LIGHT
        self._plot_item.showGrid(x=self._visible, y=self._visible, alpha=alpha)

    def _on_range_changed(self) -> None:
        if self._minor_visible:
            self._update_minor_lines()

    def _clear_minor(self) -> None:
        for line in self._minor_lines:
            self._plot_item.removeItem(line)
        self._minor_lines.clear()

    def _update_minor_lines(self) -> None:
        self._clear_minor()
        vb = self._plot_item.getViewBox()
        if not vb:
            return
        r = vb.viewRange()
        # Axe X en log : r[0] = (log10(f_min), log10(f_max))
        x_lo, x_hi = r[0][0], r[0][1]
        y_lo, y_hi = r[1][0], r[1][1]
        # Décennies visibles (en log10)
        dec_lo = int(math.floor(x_lo))
        dec_hi = int(math.ceil(x_hi))
        alpha = self.ALPHA_MINOR
        pen = pg.mkPen(255, 255, 255, alpha * 255) if self._dark_background else pg.mkPen(0, 0, 0, alpha * 255)
        for dec in range(dec_lo, dec_hi + 1):
            for sub in (2, 3, 4, 5, 6, 7, 8, 9):
                if sub == 10:
                    continue
                f_hz = sub * (10 ** dec)
                log_f = math.log10(f_hz)
                if log_f < x_lo or log_f > x_hi:
                    continue
                line = pg.InfiniteLine(pos=f_hz, angle=90, pen=pen, movable=False)
                line.setZValue(0.5)
                self._plot_item.addItem(line)
                self._minor_lines.append(line)
