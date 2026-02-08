"""
Tracé des courbes Bode (principale et brute). Module autonome viewer CSV.
"""
from typing import List, Optional

import pyqtgraph as pg
from PyQt6.QtCore import Qt

from .model import BodeCsvDataset
from .smoothing import MovingAverageSmoother


class BodeCurveDrawer:
    """Dessine la courbe principale (lissée ou brute) sur un PlotItem."""
    PEN_MAIN = pg.mkPen("#e0c040", width=2)
    PEN_RAW = pg.mkPen("#808080", width=1, style=Qt.PenStyle.DotLine)

    def __init__(self, plot_item):
        self._plot_item = plot_item
        self._curve = plot_item.plot(pen=self.PEN_MAIN)
        self._raw_curve = plot_item.plot(pen=self.PEN_RAW)
        self._raw_curve.setVisible(False)

    def set_data(
        self,
        dataset: BodeCsvDataset,
        y_linear: bool,
        smooth_window: int = 0,
        show_raw: bool = False,
    ) -> None:
        freqs = dataset.freqs_hz()
        if not freqs:
            self._curve.setData([], [])
            self._raw_curve.setData([], [])
            self._raw_curve.setVisible(False)
            return
        if y_linear:
            ys = dataset.gains_linear()
        else:
            ys = dataset.gains_db()
        if smooth_window > 0:
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

    def clear(self) -> None:
        self._curve.setData([], [])
        self._raw_curve.setData([], [])
        self._raw_curve.setVisible(False)
