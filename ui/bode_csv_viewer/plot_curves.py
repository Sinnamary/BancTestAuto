"""
Tracé des courbes Bode (principale et brute). Module autonome viewer CSV.
"""
from typing import List, Optional, Union

import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.app_logger import get_logger
from .model import BodeCsvDataset
from .smoothing import MovingAverageSmoother, smooth_savgol

logger = get_logger(__name__)


class BodeCurveDrawer:
    """Dessine la courbe principale (lissée ou brute) sur un PlotItem."""
    DEFAULT_MAIN_COLOR = "#e0c040"
    PEN_MAIN = pg.mkPen(DEFAULT_MAIN_COLOR, width=2.5)
    PEN_RAW = pg.mkPen("#909090", width=1.2, style=Qt.PenStyle.DotLine)

    def __init__(self, plot_item):
        self._plot_item = plot_item
        try:
            self._curve = plot_item.plot(pen=self.PEN_MAIN, antialias=True)
            self._raw_curve = plot_item.plot(pen=self.PEN_RAW, antialias=True)
        except TypeError:
            self._curve = plot_item.plot(pen=self.PEN_MAIN)
            self._raw_curve = plot_item.plot(pen=self.PEN_RAW)
        self._raw_curve.setVisible(False)

    def set_curve_visible(self, visible: bool) -> None:
        """Affiche ou masque la courbe principale et la courbe brute."""
        self._curve.setVisible(visible)
        self._raw_curve.setVisible(visible and self._raw_curve.isVisible())

    def set_curve_color(self, color: Union[str, QColor]) -> None:
        """Change la couleur de la courbe principale (nom, hex ou QColor)."""
        if isinstance(color, QColor):
            color = color.name()
        self._curve.setPen(pg.mkPen(color, width=2.5))

    def set_data(
        self,
        dataset: BodeCsvDataset,
        y_linear: bool,
        smooth_window: int = 0,
        show_raw: bool = False,
        smooth_savgol_flag: bool = False,
    ) -> None:
        freqs = dataset.freqs_hz()
        if not freqs:
            logger.debug("BodeCurveDrawer.set_data: pas de fréquences, courbe gain vidée")
            self._curve.setData([], [])
            self._raw_curve.setData([], [])
            self._raw_curve.setVisible(False)
            return
        if y_linear:
            ys = dataset.gains_linear()
        else:
            ys = dataset.gains_db()
        logger.debug(
            "BodeCurveDrawer.set_data: courbe GAIN | freqs Hz: [%.6g, %.6g] (%d pts) | Y: [%.6g, %.6g] | smooth=%s",
            min(freqs), max(freqs), len(freqs), min(ys), max(ys),
            f"fenêtre={smooth_window}" if smooth_window > 0 else "non",
        )
        if smooth_window > 0:
            if smooth_savgol_flag:
                ys_smooth = smooth_savgol(ys, smooth_window)
            else:
                smoother = MovingAverageSmoother(smooth_window)
                ys_smooth = smoother.smooth(ys)
            self._curve.setData(freqs, ys_smooth)
            if show_raw:
                self._raw_curve.setData(freqs, ys)
                self._raw_curve.setVisible(True)
            else:
                self._raw_curve.setData([], [])
                self._raw_curve.setVisible(False)
        else:
            self._curve.setData(freqs, ys)
            self._raw_curve.setData([], [])
            self._raw_curve.setVisible(False)
        logger.debug("BodeCurveDrawer.set_data: setData(gain) appliqué")

    def clear(self) -> None:
        self._curve.setData([], [])
        self._raw_curve.setData([], [])
        self._raw_curve.setVisible(False)
