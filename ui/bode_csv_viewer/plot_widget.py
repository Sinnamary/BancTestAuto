"""
Widget graphique Bode pour le viewer CSV. Compose grille, courbes, marqueur fc.
Aucune dépendance aux vues ou au core du banc de test.
"""
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

from .model import BodeCsvDataset
from .plot_grid import BodePlotGrid
from .plot_curves import BodeCurveDrawer
from .plot_cutoff_viz import CutoffMarkerViz
from .cutoff import Cutoff3DbFinder, CutoffResult


class BodeCsvPlotWidget(QWidget):
    """Graphique Bode semi-log dédié au visualiseur CSV."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setLabel("left", "Gain", units="dB")
        self._plot_widget.setLabel("bottom", "Fréquence", units="Hz")
        self._plot_widget.setLogMode(x=True, y=False)
        layout.addWidget(self._plot_widget)
        plot_item = self._plot_widget.getPlotItem()
        self._grid = BodePlotGrid(plot_item)
        self._curves = BodeCurveDrawer(plot_item)
        self._cutoff_viz = CutoffMarkerViz(plot_item)
        self._dataset: Optional[BodeCsvDataset] = None
        self._y_linear = False
        self._smooth_window = 0
        self._show_raw = False
        self._show_cutoff = False

    def set_dataset(self, dataset: Optional[BodeCsvDataset]) -> None:
        self._dataset = dataset
        self._refresh()

    def set_y_linear(self, y_linear: bool) -> None:
        self._y_linear = y_linear
        if y_linear:
            self._plot_widget.setLabel("left", "Gain (Us/Ue)", units="")
        else:
            self._plot_widget.setLabel("left", "Gain", units="dB")
        self._refresh()

    def set_grid_visible(self, visible: bool) -> None:
        self._grid.set_visible(visible)

    def set_smoothing(self, window: int, show_raw: bool = False) -> None:
        self._smooth_window = max(0, min(11, window))
        self._show_raw = show_raw and self._smooth_window > 0
        self._refresh()

    def set_cutoff_visible(self, visible: bool) -> None:
        self._show_cutoff = visible
        self._refresh_cutoff()

    def _refresh(self) -> None:
        if not self._dataset or self._dataset.is_empty():
            self._curves.clear()
            self._cutoff_viz.set_fc(None)
            return
        self._curves.set_data(
            self._dataset,
            y_linear=self._y_linear,
            smooth_window=self._smooth_window,
            show_raw=self._show_raw,
        )
        self._refresh_cutoff()
        self._cutoff_viz.update_label_position()

    def _refresh_cutoff(self) -> None:
        if not self._show_cutoff or not self._dataset or self._dataset.is_empty():
            self._cutoff_viz.set_fc(None)
            return
        finder = Cutoff3DbFinder()
        result = finder.find(self._dataset)
        if result:
            self._cutoff_viz.set_fc(result.fc_hz)
        else:
            self._cutoff_viz.set_fc(None)
        self._cutoff_viz.update_label_position()

    def auto_range(self) -> None:
        if self._dataset and not self._dataset.is_empty():
            self._plot_widget.getViewBox().enableAutoRange()
            self._plot_widget.getViewBox().autoRange()

    def export_png(self, path: str) -> bool:
        try:
            self._plot_widget.getViewBox().setBackgroundColor("k")
            exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
            exporter.export(path)
            return True
        except Exception:
            return False
