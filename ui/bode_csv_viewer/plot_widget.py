"""
Widget graphique Bode pour le viewer CSV. Compose grille, courbes, marqueurs.
Zoom (molette, zoom zone), pan, réglage des échelles. Délègue à plot_* pour la logique.
"""
from typing import Optional, Tuple, Union

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView
from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QColor
import pyqtgraph as pg

from core.app_logger import get_logger

from .model import BodeCsvDataset
from .plot_grid import BodePlotGrid
from .plot_curves import BodeCurveDrawer
from .plot_cutoff_viz import CutoffMarkerViz
from .plot_hover import create_hover_label, update_hover_from_viewport_event
from .plot_peaks import BodePeaksOverlay
from .plot_range import compute_data_range, apply_view_range, read_view_range
from .plot_style import apply_axis_fonts, apply_background_style, BG_DARK, BG_LIGHT

logger = get_logger(__name__)


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
        self._plot_widget.getPlotItem().getAxis("bottom").enableAutoSIPrefix(False)
        vb = self._plot_widget.getViewBox()
        vb.setMouseMode(vb.PanMode)
        vb.disableAutoRange()
        try:
            vb.setAntialiasing(True)
        except Exception:
            pass
        layout.addWidget(self._plot_widget)
        plot_item = self._plot_widget.getPlotItem()
        self._grid = BodePlotGrid(plot_item)
        self._curves = BodeCurveDrawer(plot_item)
        self._cutoff_viz = CutoffMarkerViz(plot_item)
        self._peaks_overlay = BodePeaksOverlay(plot_item)
        self._hover_label: Optional[pg.TextItem] = None
        self._hover_filter_installed = False
        self._setup_hover()
        self._dataset: Optional[BodeCsvDataset] = None
        self._y_linear = False
        self._smooth_window = 0
        self._last_target_gain_db: Optional[float] = None
        self._last_target_fc_list: Optional[list] = None
        self._show_raw = False
        self._smooth_savgol = False
        self._background_dark = True
        apply_axis_fonts(plot_item)
        self._apply_background_style()

    def _setup_hover(self) -> None:
        plot_item = self._plot_widget.getPlotItem()
        self._hover_label = create_hover_label(plot_item)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._hover_filter_installed and self._plot_widget is not None:
            vb = self._plot_widget.getViewBox()
            scene = vb.scene()
            if scene is not None:
                views = scene.views()
                if views:
                    views[0].viewport().installEventFilter(self)
                    self._hover_filter_installed = True

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseMove:
            update_hover_from_viewport_event(
                obj, event, self._plot_widget, self._hover_label, self._y_linear
            )
        return super().eventFilter(obj, event)

    def set_dataset(self, dataset: Optional[BodeCsvDataset]) -> None:
        self._dataset = dataset
        self._refresh()
        if self._dataset and not self._dataset.is_empty():
            self.auto_range()

    def set_y_linear(self, y_linear: bool) -> None:
        self._y_linear = y_linear
        if y_linear:
            self._plot_widget.setLabel("left", "Gain (Us/Ue)", units="")
        else:
            self._plot_widget.setLabel("left", "Gain", units="dB")
        self._refresh()
        if self._last_target_gain_db is not None:
            self.set_target_gain_search(self._last_target_gain_db, self._last_target_fc_list)

    def set_grid_visible(self, visible: bool) -> None:
        self._grid.set_visible(visible)

    def set_minor_grid_visible(self, visible: bool) -> None:
        self._grid.set_minor_visible(visible)

    def set_background_dark(self, dark: bool) -> None:
        self._background_dark = dark
        self._apply_background_style()

    def _apply_background_style(self) -> None:
        pi = self._plot_widget.getPlotItem()
        vb = self._plot_widget.getViewBox()
        apply_background_style(pi, vb, self._background_dark, self._grid, self._hover_label)

    def set_curve_color(self, color: Union[str, QColor]) -> None:
        self._curves.set_curve_color(color)

    def set_smoothing(
        self, window: int, show_raw: bool = False, use_savgol: bool = False
    ) -> None:
        self._smooth_window = max(0, min(11, window))
        self._show_raw = show_raw and self._smooth_window > 0
        self._smooth_savgol = use_savgol
        self._refresh()

    def set_peaks_visible(self, visible: bool) -> None:
        self._peaks_overlay.set_visible(visible)
        self._peaks_overlay.update(self._dataset, self._y_linear)

    def set_target_gain_search(
        self, gain_db: Optional[float], fc_hz_list: Optional[list] = None
    ) -> None:
        self._last_target_gain_db = gain_db
        self._last_target_fc_list = (fc_hz_list or []) if gain_db is not None else None
        if gain_db is None:
            self._cutoff_viz.set_target_gain(None)
            self._cutoff_viz.set_target_gain_frequencies([])
        else:
            y_display = (10 ** (gain_db / 20.0)) if self._y_linear else gain_db
            self._cutoff_viz.set_target_gain(gain_db, f"{gain_db:.1f} dB", y_display=y_display)
            self._cutoff_viz.set_target_gain_frequencies(fc_hz_list or [])

    def _refresh(self) -> None:
        if not self._dataset or self._dataset.is_empty():
            self._curves.clear()
            self._cutoff_viz.set_level(None)
            self._cutoff_viz.set_cutoff_frequencies([])
            self._peaks_overlay.update(None, self._y_linear)
            return
        self._curves.set_data(
            self._dataset,
            y_linear=self._y_linear,
            smooth_window=self._smooth_window,
            show_raw=self._show_raw,
            smooth_savgol_flag=self._smooth_savgol,
        )
        self._cutoff_viz.set_level(None)
        self._cutoff_viz.set_cutoff_frequencies([])
        self._peaks_overlay.update(self._dataset, self._y_linear)
        self._cutoff_viz.update_label_position()

    def get_data_range(self) -> Optional[Tuple[float, float, float, float]]:
        if not self._dataset or self._dataset.is_empty():
            return None
        freqs = self._dataset.freqs_hz()
        ys = self._dataset.gains_linear() if self._y_linear else self._dataset.gains_db()
        return compute_data_range(freqs, ys)

    def auto_range(self) -> None:
        r = self.get_data_range()
        if r is not None:
            self.set_view_range(r[0], r[1], r[2], r[3])
        else:
            vb = self._plot_widget.getViewBox()
            vb.enableAutoRange()
            vb.autoRange()

    def set_view_range(
        self, x_min: float, x_max: float, y_min: float, y_max: float
    ) -> None:
        vb = self._plot_widget.getViewBox()
        log_mode_x = vb.state.get("logMode", [False, False])[0]
        apply_view_range(vb, x_min, x_max, y_min, y_max, log_mode_x=log_mode_x)
        self._cutoff_viz.update_label_position()

    def set_rect_zoom_mode(self, enabled: bool) -> None:
        vb = self._plot_widget.getViewBox()
        vb.setMouseMode(vb.RectMode if enabled else vb.PanMode)

    def get_view_range(self) -> Tuple[float, float, float, float]:
        vb = self._plot_widget.getViewBox()
        log_mode_x = vb.state.get("logMode", [False, False])[0]
        fallback = self.get_data_range()
        out = read_view_range(vb, log_mode_x=log_mode_x, fallback=fallback)
        logger.debug(
            "Bode plot get_view_range: x=[%.6g, %.6g], y=[%.6g, %.6g]",
            out[0], out[1], out[2], out[3],
        )
        return out

    def export_png(self, path: str) -> bool:
        try:
            vb = self._plot_widget.getViewBox()
            vb.setBackgroundColor(BG_DARK if self._background_dark else BG_LIGHT)
            exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
            exporter.export(path)
            return True
        except Exception:
            return False
