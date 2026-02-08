"""
Affichage des marqueurs pics (maxima) et creux (minima) locaux sur le graphique Bode.
Module autonome, utilisé par BodeCsvPlotWidget.
"""
from typing import Any, Optional

import pyqtgraph as pg

from .model import BodeCsvDataset

try:
    from core.bode_utils import find_peaks_and_valleys
except ImportError:
    def find_peaks_and_valleys(*_args, **_kwargs):
        return []


class BodePeaksOverlay:
    """Gère les scatter plots pics (jaune) et creux (bleu) sur un PlotItem."""

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._peaks_scatter: Optional[pg.ScatterPlotItem] = None
        self._valleys_scatter: Optional[pg.ScatterPlotItem] = None
        self._visible = False

    def set_visible(self, visible: bool) -> None:
        self._visible = bool(visible)

    def update(
        self,
        dataset: Optional[BodeCsvDataset],
        y_linear: bool,
    ) -> None:
        """
        Met à jour les marqueurs à partir du dataset.
        Si visible=False ou dataset vide, masque les points.
        """
        self._ensure_scatters()
        if not self._visible or not dataset or dataset.is_empty():
            self._peaks_scatter.setData([], [])
            self._valleys_scatter.setData([], [])
            return
        freqs = dataset.freqs_hz()
        gains = dataset.gains_db()
        peaks_valleys = find_peaks_and_valleys(freqs, gains, order=3)
        px, py = [], []
        vx, vy = [], []
        for f, g_db, kind in peaks_valleys:
            g_show = (10 ** (g_db / 20.0)) if y_linear else g_db
            if kind == "pic":
                px.append(f)
                py.append(g_show)
            else:
                vx.append(f)
                vy.append(g_show)
        self._peaks_scatter.setData(px, py)
        self._valleys_scatter.setData(vx, vy)

    def _ensure_scatters(self) -> None:
        if self._peaks_scatter is None:
            self._peaks_scatter = pg.ScatterPlotItem(
                size=10,
                pen=pg.mkPen(None),
                brush=pg.mkBrush(255, 200, 0, 200),
                symbol="o",
                zValue=8,
            )
            self._plot_item.addItem(self._peaks_scatter)
        if self._valleys_scatter is None:
            self._valleys_scatter = pg.ScatterPlotItem(
                size=10,
                pen=pg.mkPen(None),
                brush=pg.mkBrush(100, 200, 255, 200),
                symbol="o",
                zValue=8,
            )
            self._plot_item.addItem(self._valleys_scatter)
