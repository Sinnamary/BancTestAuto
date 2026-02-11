"""
Widget graphique Bode pour le viewer CSV. Compose grille, courbes, marqueurs.
Zoom (molette, zoom zone), pan, réglage des échelles. Délègue à plot_* pour la logique.
"""
import math
from typing import Optional, Tuple, Union

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView
from PyQt6.QtCore import QEvent, Qt
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
        logger.debug(
            "Bode plot __init__: main_vb id=%s mouseMode initial=%s (PanMode=3, RectMode=1)",
            id(vb), vb.state.get("mouseMode"),
        )
        vb.disableAutoRange()
        # Plage X par défaut raisonnable (évite 10^-100..10^150 en mode log au premier affichage)
        apply_view_range(vb, 1.0, 1e6, -40.0, 5.0, log_mode_x=True)
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
        self._show_gain = True
        self._show_phase = True
        # Axe secondaire (phase, à droite) : ViewBox + courbe phase
        self._plot_item = plot_item
        self._main_vb = plot_item.getViewBox()
        plot_item.showAxis("right")
        self._right_vb = pg.ViewBox(enableMouse=False)  # Souris ignorée → zoom sur zone et pan sur le ViewBox principal
        # Même échelle X que le gain : log10(Hz) pour que la courbe phase utilise les mêmes abscisses.
        # Utiliser setLogMode() pour que le ViewBox mette à jour childTransform (rendu), pas seulement state.
        try:
            if hasattr(self._right_vb, "setLogMode"):
                # API ViewBox : setLogMode(axis, logMode) avec axis 0=X, 1=Y
                self._right_vb.setLogMode(0, True)   # X en log10(Hz)
                self._right_vb.setLogMode(1, False)  # Y linéaire (°)
            else:
                self._right_vb.state["logMode"] = [True, False]
        except Exception as e:
            logger.warning("Bode plot __init__: setLogMode sur right_vb non disponible, fallback state: %s", e)
            self._right_vb.state["logMode"] = [True, False]
        self._right_vb._matrixNeedsUpdate = True
        try:
            self._right_vb.updateMatrix()
        except Exception:
            pass
        logger.debug(
            "Bode plot __init__: right_vb créé avec logMode X=True (log10(Hz)) | state.logMode=%s",
            self._right_vb.state.get("logMode"),
        )
        plot_item.scene().addItem(self._right_vb)
        self._right_vb.setZValue(10)  # Dessiner au premier plan (courbe phase visible)
        # Laisser passer les événements souris au ViewBox principal (zoom zone, pan, molette)
        self._right_vb.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._right_vb.setAcceptHoverEvents(False)
        logger.debug(
            "Bode plot __init__: right_vb acceptedMouseButtons=%s acceptHoverEvents=%s (pour laisser zoom zone au main)",
            self._right_vb.acceptedMouseButtons(), self._right_vb.acceptHoverEvents(),
        )
        plot_item.getAxis("right").linkToView(self._right_vb)
        self._right_vb.setXLink(self._main_vb)
        self._phase_curve = pg.PlotDataItem(pen=pg.mkPen("#40c0c0", width=2), antialias=True)
        if hasattr(self._phase_curve, "setLogMode"):
            self._phase_curve.setLogMode(True, False)  # X log, Y linéaire (cohérent avec right_vb)
        self._phase_curve.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._phase_curve.setAcceptHoverEvents(False)
        self._right_vb.addItem(self._phase_curve)
        self._right_vb.setVisible(False)
        plot_item.getAxis("right").setVisible(False)
        plot_item.getAxis("right").setLabel("Phase", units="°")

        def _update_right_vb_geometry():
            self._right_vb.setGeometry(self._main_vb.sceneBoundingRect())
            self._right_vb.linkedViewChanged(self._main_vb, self._right_vb.XAxis)

        self._main_vb.sigResized.connect(_update_right_vb_geometry)
        self._main_vb.sigRangeChanged.connect(_update_right_vb_geometry)  # Gain et phase même X (zoom/pan/limites)
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
        self._right_vb.setGeometry(self._main_vb.sceneBoundingRect())
        self._right_vb.linkedViewChanged(self._main_vb, self._right_vb.XAxis)
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
        self._right_vb.setVisible(visible and has_phase)
        self._plot_item.getAxis("right").setVisible(visible and has_phase)
        if has_phase:
            self._phase_curve.setVisible(visible)
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
        if not self._dataset or self._dataset.is_empty():
            logger.debug("Bode plot _refresh: dataset vide → courbes vidées")
            self._curves.clear()
            self._phase_curve.setData([], [])
            self._right_vb.setVisible(False)
            self._plot_item.getAxis("right").setVisible(False)
            self._cutoff_viz.set_level(None)
            self._cutoff_viz.set_cutoff_frequencies([])
            self._peaks_overlay.update(None, self._y_linear)
            return
        self._curves.set_curve_visible(self._show_gain)
        self._curves.set_data(
            self._dataset,
            y_linear=self._y_linear,
            smooth_window=self._smooth_window,
            show_raw=self._show_raw,
            smooth_savgol_flag=self._smooth_savgol,
        )
        has_phase = self._dataset.has_phase()
        if has_phase:
            freqs = self._dataset.freqs_hz()
            phases = self._dataset.phases_deg()
            ys_phase = [(p if p is not None else 0.0) for p in phases]
            logger.debug(
                "Bode plot _refresh PHASE: entrée | freqs Hz [%.6g, %.6g] (%d pts) | phase ° [%.6g, %.6g] | right_vb.logMode=%s",
                min(freqs), max(freqs), len(freqs), min(ys_phase), max(ys_phase),
                self._right_vb.state.get("logMode"),
            )
            self._phase_curve.setData(freqs, ys_phase)
            logger.debug("Bode plot _refresh PHASE: setData(freqs, ys_phase) appelé")
            self._phase_curve.setVisible(self._show_phase)
            self._right_vb.setVisible(self._show_phase)
            self._plot_item.getAxis("right").setVisible(self._show_phase)
            # Diagnostic visibilité courbe phase
            try:
                bounds = self._phase_curve.dataBounds(ax=0), self._phase_curve.dataBounds(ax=1)
                logger.debug(
                    "Bode plot _refresh PHASE: visibilité | show_phase=%s phase_curve.isVisible=%s right_vb.isVisible=%s axis_right.isVisible=%s | dataBounds(ax0)=%s dataBounds(ax1)=%s",
                    self._show_phase,
                    self._phase_curve.isVisible(),
                    self._right_vb.isVisible(),
                    self._plot_item.getAxis("right").isVisible(),
                    bounds[0],
                    bounds[1],
                )
            except Exception as e:
                logger.debug("Bode plot _refresh PHASE: visibilité (exception) %s", e)
            self._right_vb.setGeometry(self._main_vb.sceneBoundingRect())
            self._right_vb.linkedViewChanged(self._main_vb, self._right_vb.XAxis)
            main_x, main_y = self._main_vb.viewRange()[0], self._main_vb.viewRange()[1]
            try:
                hz_lo = 10.0 ** max(-307, min(308, main_x[0]))
                hz_hi = 10.0 ** max(-307, min(308, main_x[1]))
            except Exception:
                hz_lo, hz_hi = float("nan"), float("nan")
            logger.debug(
                "Bode plot _refresh PHASE: main_vb.viewRange (vue) X=%s (≈ %.6g..%.6g Hz) | Y=%s",
                main_x, hz_lo, hz_hi, main_y,
            )
            # Pas d'autoRange sur right_vb : il n'a pas logMode en ancienne config et remettait main en 10^-300..10^300
            # X = plage main (log10 Hz) ; Y = plage phase depuis données
            x_range = list(self._main_vb.viewRange()[0])
            y_phase_vals = [y for y in ys_phase if math.isfinite(y)]
            if y_phase_vals:
                y_lo, y_hi = min(y_phase_vals), max(y_phase_vals)
                dy = (y_hi - y_lo) * 0.05 or 1.0
                y_range = (y_lo - dy, y_hi + dy)
            else:
                y_range = (-90.0, 0.0)
            logger.debug(
                "Bode plot _refresh PHASE: setRange right_vb | xRange=%s (log10 Hz, copié main) | yRange=%s (phase °)",
                x_range, y_range,
            )
            self._right_vb.setRange(
                xRange=tuple(x_range),
                yRange=y_range,
                padding=0,  # pas de padding pour éviter dérive X et garder même vue que main
                update=True,
                disableAutoRange=True,
            )
            # Forcer recalcul du transform (log X) pour que la courbe phase soit rendue correctement
            self._right_vb._matrixNeedsUpdate = True
            try:
                self._right_vb.updateMatrix()
            except Exception:
                pass
            logger.debug(
                "Bode plot _refresh PHASE: sortie | right_vb.viewRange X=%s Y=%s | right_vb.zValue=%s sceneBoundingRect=%s",
                self._right_vb.viewRange()[0],
                self._right_vb.viewRange()[1],
                self._right_vb.zValue(),
                self._right_vb.sceneBoundingRect(),
            )
        else:
            self._phase_curve.setData([], [])
            self._right_vb.setVisible(False)
            self._plot_item.getAxis("right").setVisible(False)
        self._cutoff_viz.set_level(None)
        self._cutoff_viz.set_cutoff_frequencies([])
        self._peaks_overlay.update(self._dataset, self._y_linear)
        self._cutoff_viz.update_label_position()
        logger.debug("Bode plot _refresh: sortie")

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
        # Resynchroniser le ViewBox phase (axe droit) avec le zoom X et la géométrie
        self._right_vb.setGeometry(self._main_vb.sceneBoundingRect())
        self._right_vb.linkedViewChanged(self._main_vb, self._right_vb.XAxis)
        logger.debug(
            "Bode plot set_view_range: linkedViewChanged(main, right.XAxis) | main_vb.viewRange X=%s",
            vb.viewRange()[0],
        )
        self._cutoff_viz.update_label_position()

    def set_rect_zoom_mode(self, enabled: bool) -> None:
        vb = self._plot_widget.getViewBox()
        mode_avant = vb.state.get("mouseMode", "?")
        mode_name = "RectMode" if enabled else "PanMode"
        mode_valeur = vb.RectMode if enabled else vb.PanMode
        logger.debug(
            "Bode plot set_rect_zoom_mode: entrée enabled=%s → mode=%s (valeur=%s)",
            enabled, mode_name, mode_valeur,
        )
        logger.debug(
            "Bode plot set_rect_zoom_mode: main_vb id=%s mouseMode avant=%s (RectMode=1 PanMode=3)",
            id(vb), mode_avant,
        )
        vb.setMouseMode(mode_valeur)
        mode_apres = vb.state.get("mouseMode", "?")
        try:
            right_btns = self._right_vb.acceptedMouseButtons()
        except Exception:
            right_btns = "?"
        logger.debug(
            "Bode plot set_rect_zoom_mode: sortie mouseMode après=%s | right_vb acceptedMouseButtons=%s",
            mode_apres, right_btns,
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
