"""
Widget graphique Bode pour le viewer CSV. Compose canvas, phase overlay, zoom, grille, courbes.
Délègue à zoom_mode, viewbox_phase, plot_canvas et plot_* pour faciliter le debug.
"""
from typing import Optional, Tuple, Union

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor, QMouseEvent
import pyqtgraph as pg

from core.app_logger import get_logger

from .model import BodeCsvDataset
from .plot_canvas import create_bode_canvas
from .plot_grid import BodePlotGrid
from .plot_curves import BodeCurveDrawer
from .plot_cutoff_viz import CutoffMarkerViz
from .plot_hover import create_hover_label, update_hover_from_viewport_event
from .plot_peaks import BodePeaksOverlay
from .plot_range import compute_data_range, apply_view_range, read_view_range
from .plot_style import apply_axis_fonts, apply_background_style, BG_DARK, BG_LIGHT
from .viewbox_phase import PhaseOverlay
from .zoom_mode import ZoomModeController
from .plot_refresh import refresh_bode_plot

logger = get_logger(__name__)


class BodeCsvPlotWidget(QWidget):
    """Graphique Bode semi-log dédié au visualiseur CSV."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._plot_widget, plot_item, self._main_vb = create_bode_canvas()
        layout.addWidget(self._plot_widget)
        self._plot_item = plot_item
        self._grid = BodePlotGrid(plot_item)
        self._curves = BodeCurveDrawer(plot_item)
        self._cutoff_viz = CutoffMarkerViz(plot_item)
        self._peaks_overlay = BodePeaksOverlay(plot_item)
        self._zoom_controller = ZoomModeController(self._main_vb)
        self._phase_overlay = PhaseOverlay(plot_item, self._main_vb)
        self._curves.set_accept_mouse(False)
        self._hover_label: Optional[pg.TextItem] = None
        self._hover_filter_installed = False
        self._graphics_view = None  # rempli dans showEvent pour eventFilter (hover)
        self._setup_hover()
        self._dataset: Optional[BodeCsvDataset] = None
        self._y_linear = False
        self._smooth_window = 0
        self._last_target_gain_db: Optional[float] = None
        self._last_target_fc_list: Optional[list] = None
        self._show_raw = False
        self._smooth_savgol = False
        self._background_dark = True
        self._show_gain = True
        self._show_phase = True
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
                    self._graphics_view = views[0]
                    self._graphics_view.viewport().installEventFilter(self)
                    self._hover_filter_installed = True
                    logger.debug(
                        "Bode zoom: eventFilter installé sur viewport view=%s",
                        id(self._graphics_view),
                    )

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseMove:
            update_hover_from_viewport_event(
                obj, event, self._plot_widget, self._hover_label, self._y_linear
            )
        # Logs debug zoom: quand zoom zone est coché, log Press/Release et l'item sous le curseur
        if (
            isinstance(event, QMouseEvent)
            and event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease)
            and self._zoom_controller.is_rect_zoom_enabled()
            and self._graphics_view is not None
        ):
            scene = self._main_vb.scene()
            if scene is not None:
                try:
                    pt = event.position().toPoint() if hasattr(event.position(), "toPoint") else event.pos()
                    scene_pt = self._graphics_view.mapToScene(pt)
                    item = scene.itemAt(scene_pt, self._graphics_view.transform())
                    type_name = "Press" if event.type() == QEvent.Type.MouseButtonPress else "Release"
                    logger.debug(
                        "Bode zoom: eventFilter %s pos=(%.0f,%.0f) → item=%s id=%s (pour zoom rect, il faudrait main_vb ou enfant)",
                        type_name, scene_pt.x(), scene_pt.y(),
                        type(item).__name__ if item else None, id(item) if item else None,
                    )
                except Exception as e:
                    logger.debug("Bode zoom: eventFilter log itemAt exception: %s", e)
        return super().eventFilter(obj, event)

    def set_dataset(self, dataset: Optional[BodeCsvDataset]) -> None:
        logger.debug("Bode plot set_dataset: entrée | dataset=%s", (len(dataset.freqs_hz()) if (dataset and not dataset.is_empty()) else 0))
        self._dataset = dataset
        if self._dataset and not self._dataset.is_empty():
            freqs = self._dataset.freqs_hz()
            logger.debug(
                "Bode plot set_dataset: N=%d pts | freqs Hz [%.6g, %.6g] | has_phase=%s",
                len(freqs), min(freqs), max(freqs), self._dataset.has_phase(),
            )
        self._refresh()
        if self._dataset and not self._dataset.is_empty():
            logger.debug("Bode plot set_dataset: appel auto_range()")
            self.auto_range()
        self._phase_overlay.right_vb.setGeometry(self._main_vb.sceneBoundingRect())
        self._phase_overlay.right_vb.linkedViewChanged(self._main_vb, self._phase_overlay.right_vb.XAxis)
        logger.debug("Bode plot set_dataset: sortie | main_vb.viewRange X=%s", self._main_vb.viewRange()[0])

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

    def set_show_gain(self, visible: bool) -> None:
        """Affiche ou masque la courbe de gain (axe gauche)."""
        self._show_gain = visible
        self._curves.set_curve_visible(visible)
        self._refresh()

    def set_show_phase(self, visible: bool) -> None:
        """Affiche ou masque la courbe de phase (axe droit) et l'axe droit."""
        logger.debug("Bode plot set_show_phase: visible=%s (has_phase=%s)", visible, bool(self._dataset and self._dataset.has_phase()))
        self._show_phase = visible
        has_phase = self._dataset and self._dataset.has_phase()
        self._phase_overlay.set_visible(visible and has_phase)
        self._refresh()

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
        logger.debug("Bode plot _refresh: entrée | dataset=%s show_gain=%s show_phase=%s", self._dataset is not None and not self._dataset.is_empty(), self._show_gain, self._show_phase)
        refresh_bode_plot(self)

    def get_data_range(self) -> Optional[Tuple[float, float, float, float]]:
        if not self._dataset or self._dataset.is_empty():
            logger.debug("Bode plot get_data_range: dataset vide → None")
            return None
        freqs = self._dataset.freqs_hz()
        ys = self._dataset.gains_linear() if self._y_linear else self._dataset.gains_db()
        r = compute_data_range(freqs, ys)
        if r is not None:
            logger.debug("Bode plot get_data_range: (x_min=%.6g, x_max=%.6g, y_min=%.6g, y_max=%.6g) Hz/Gain", r[0], r[1], r[2], r[3])
        return r

    def auto_range(self) -> None:
        r = self.get_data_range()
        if r is not None:
            logger.debug(
                "Bode plot auto_range: applique plage données | F [%.6g, %.6g] Hz | Gain [%.6g, %.6g]",
                r[0], r[1], r[2], r[3],
            )
            self.set_view_range(r[0], r[1], r[2], r[3])
        else:
            logger.debug("Bode plot auto_range: pas de plage, enableAutoRange sur main vb")
            vb = self._plot_widget.getViewBox()
            vb.enableAutoRange()
            vb.autoRange()

    def set_view_range(
        self, x_min: float, x_max: float, y_min: float, y_max: float
    ) -> None:
        vb = self._plot_widget.getViewBox()
        log_mode_x = vb.state.get("logMode", [False, False])[0]
        logger.debug(
            "Bode plot set_view_range: main_vb | x_min=%.6g x_max=%.6g y_min=%.6g y_max=%.6g | log_mode_x=%s",
            x_min, x_max, y_min, y_max, log_mode_x,
        )
        apply_view_range(vb, x_min, x_max, y_min, y_max, log_mode_x=log_mode_x)
        self._phase_overlay.right_vb.setGeometry(self._main_vb.sceneBoundingRect())
        self._phase_overlay.right_vb.linkedViewChanged(self._main_vb, self._phase_overlay.right_vb.XAxis)
        logger.debug(
            "Bode plot set_view_range: linkedViewChanged(main, right.XAxis) | main_vb.viewRange X=%s",
            vb.viewRange()[0],
        )
        self._cutoff_viz.update_label_position()

    def set_rect_zoom_mode(self, enabled: bool) -> None:
        """Zoom sur zone (True) ou pan (False). En mode zoom, le ViewBox phase passe derrière (z) pour que le main reçoive la souris, et le fond du main est rendu transparent pour que la phase reste visible."""
        logger.debug("Bode plot set_rect_zoom_mode: entrée enabled=%s", enabled)
        self._zoom_controller.set_rect_zoom_enabled(enabled)
        self._phase_overlay.set_zoom_zone_active(enabled)
        if enabled:
            self._main_vb.setBackgroundColor(None)
        else:
            self._apply_background_style()
        # Logs debug: état final pour diagnostiquer zoom inactif
        main_mode = self._main_vb.state.get("mouseMode")
        main_z = self._main_vb.zValue() if hasattr(self._main_vb, "zValue") else "?"
        right_z = self._phase_overlay.right_vb.zValue() if hasattr(self._phase_overlay.right_vb, "zValue") else "?"
        logger.debug(
            "Bode plot set_rect_zoom_mode: sortie mode=%s | main_vb.zValue=%s right_vb.zValue=%s (main doit être au-dessus pour recevoir la souris)",
            main_mode, main_z, right_z,
        )

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
