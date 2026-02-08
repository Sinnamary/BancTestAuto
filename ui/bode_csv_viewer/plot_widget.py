"""
Widget graphique Bode pour le viewer CSV. Compose grille, courbes, marqueur fc.
Zoom (molette, zoom zone), pan, réglage des échelles. Aucune dépendance au banc de test.
"""
import math
from typing import Optional, Tuple, Union

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import QEvent, QPointF
import pyqtgraph as pg

from core.app_logger import get_logger

logger = get_logger(__name__)

# Polices pour une bonne lisibilité des échelles (rapport/gain et fréquence)
_AXIS_LABEL_FONT_SIZE = 11
_TICK_LABEL_FONT_SIZE = 10

from .model import BodeCsvDataset
from .plot_grid import BodePlotGrid
from .plot_curves import BodeCurveDrawer
from .plot_cutoff_viz import CutoffMarkerViz, LEVEL_DB, LEVEL_LINEAR
from .cutoff import Cutoff3DbFinder

try:
    from core.bode_utils import find_peaks_and_valleys
except ImportError:
    def find_peaks_and_valleys(*_args, **_kwargs):
        return []

# Marge relative pour l'auto-range (évite que la courbe colle aux bords)
_AUTO_RANGE_MARGIN = 0.05

# Couleurs fond : noir = thème sombre, blanc = thème clair
_BG_DARK = "k"
_BG_LIGHT = "w"
# Thème sombre : axes et texte en gris clair
_AXIS_PEN_DARK = pg.mkPen("#c0c0c0")
# Thème clair : axes et texte en noir pour forte lisibilité sur fond blanc
_AXIS_PEN_LIGHT = pg.mkPen("#000000")
_TICK_LABEL_COLOR_LIGHT = "#000000"


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
        # Désactiver le préfixe SI sur l'axe X : en mode log il fausse l'échelle (ex. "e27Hz", 10^23…).
        # On affiche toujours les fréquences en Hz (0,1 ; 1 ; 10 ; 100 ; …).
        self._plot_widget.getPlotItem().getAxis("bottom").enableAutoSIPrefix(False)
        vb = self._plot_widget.getViewBox()
        vb.setMouseMode(vb.PanMode)
        # Désactiver l'auto-range dès l'init pour que "Appliquer les limites" ne soit pas écrasé.
        vb.disableAutoRange()
        layout.addWidget(self._plot_widget)
        plot_item = self._plot_widget.getPlotItem()
        self._grid = BodePlotGrid(plot_item)
        self._curves = BodeCurveDrawer(plot_item)
        self._cutoff_viz = CutoffMarkerViz(plot_item)
        self._hover_label: Optional[pg.TextItem] = None
        self._hover_filter_installed = False
        self._setup_hover()
        self._peaks_scatter: Optional[pg.ScatterPlotItem] = None
        self._valleys_scatter: Optional[pg.ScatterPlotItem] = None
        self._show_peaks = False
        self._smooth_savgol = False
        self._dataset: Optional[BodeCsvDataset] = None
        self._y_linear = False
        self._smooth_window = 0
        self._show_raw = False
        self._show_cutoff = False
        self._background_dark = True  # Noir par défaut
        self._apply_axis_fonts()
        self._apply_background_style()

    def _setup_hover(self) -> None:
        """Affiche (f, gain) au survol du graphique pour faciliter la lecture."""
        plot_item = self._plot_widget.getPlotItem()
        self._hover_label = pg.TextItem(anchor=(0, 1), text="")
        self._hover_label.setZValue(20)
        self._hover_label.setVisible(False)
        plot_item.addItem(self._hover_label)
        # Installation du filtre au premier affichage (scène peut être None à l'init)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_hover_filter_installed", False) and self._plot_widget is not None:
            vb = self._plot_widget.getViewBox()
            scene = vb.scene()
            if scene is not None:
                views = scene.views()
                if views:
                    views[0].viewport().installEventFilter(self)
                    self._hover_filter_installed = True

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseMove:
            self._on_mouse_moved_from_event(obj, event)
        return super().eventFilter(obj, event)

    def _on_mouse_moved_from_event(self, viewport, event) -> None:
        """Convertit l'événement souris en position scène et met à jour le survol."""
        view = viewport.parent()
        if not isinstance(view, QGraphicsView):
            return
        # event.pos() est en coordonnées viewport → view → scene
        pos_in_view = viewport.mapTo(view, event.pos())
        scene_pos = view.mapToScene(pos_in_view)
        self._on_mouse_moved(scene_pos)

    def _on_mouse_moved(self, scene_pos) -> None:
        if self._hover_label is None:
            return
        vb = self._plot_widget.getViewBox()
        if not vb.sceneBoundingRect().contains(scene_pos):
            self._hover_label.setVisible(False)
            return
        # Coordonnées dans le repère du graphique (axe X en log = log10(Hz))
        p = vb.mapSceneToView(scene_pos)
        x_data, y_data = p.x(), p.y()
        # En mode log X, pyqtgraph utilise log10(Hz) en interne
        if self._plot_widget.getViewBox().state.get("logMode", [False, False])[0]:
            try:
                f_hz = 10.0 ** float(x_data)
            except (TypeError, ValueError, OverflowError):
                self._hover_label.setVisible(False)
                return
        else:
            f_hz = float(x_data)
        if f_hz <= 0 or not math.isfinite(f_hz):
            self._hover_label.setVisible(False)
            return
        unit = "dB" if not self._y_linear else "Us/Ue"
        if f_hz >= 1000:
            f_str = f"{f_hz / 1000:.3f} kHz"
        else:
            f_str = f"{f_hz:.2f} Hz"
        self._hover_label.setText(f"f = {f_str}  |  G = {y_data:.2f} {unit}")
        self._hover_label.setPos(x_data, y_data)
        self._hover_label.setVisible(True)

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

    def set_grid_visible(self, visible: bool) -> None:
        self._grid.set_visible(visible)

    def set_minor_grid_visible(self, visible: bool) -> None:
        self._grid.set_minor_visible(visible)

    def set_background_dark(self, dark: bool) -> None:
        """True = fond noir, False = fond blanc."""
        self._background_dark = dark
        self._apply_background_style()

    def _apply_axis_fonts(self) -> None:
        """Applique des polices lisibles pour les libellés et graduations des axes."""
        pi = self._plot_widget.getPlotItem()
        label_font = QFont()
        label_font.setPointSize(_AXIS_LABEL_FONT_SIZE)
        label_font.setBold(True)
        tick_font = QFont()
        tick_font.setPointSize(_TICK_LABEL_FONT_SIZE)
        for ax_name in ("left", "bottom"):
            ax_item = pi.getAxis(ax_name)
            ax_item.tickFont = tick_font
            if hasattr(ax_item, "label") and ax_item.label is not None:
                ax_item.label.setFont(label_font)
        pi.getAxis("left").setWidth(48)
        pi.getAxis("bottom").setHeight(42)

    def _apply_background_style(self) -> None:
        vb = self._plot_widget.getViewBox()
        pi = self._plot_widget.getPlotItem()
        self._grid.set_dark_background(self._background_dark)
        if self._background_dark:
            vb.setBackgroundColor(_BG_DARK)
            for ax in ("left", "bottom"):
                ax_item = pi.getAxis(ax)
                ax_item.setPen(_AXIS_PEN_DARK)
                ax_item.setTextPen(_AXIS_PEN_DARK)
                if hasattr(ax_item, "label") and ax_item.label is not None:
                    ax_item.label.setDefaultTextColor(QColor("#c0c0c0"))
        else:
            vb.setBackgroundColor(_BG_LIGHT)
            for ax in ("left", "bottom"):
                ax_item = pi.getAxis(ax)
                ax_item.setPen(_AXIS_PEN_LIGHT)
                ax_item.setTextPen(_AXIS_PEN_LIGHT)
                if hasattr(ax_item, "label") and ax_item.label is not None:
                    ax_item.label.setDefaultTextColor(QColor(_TICK_LABEL_COLOR_LIGHT))

    def set_curve_color(self, color: Union[str, QColor]) -> None:
        """Change la couleur de la courbe principale."""
        self._curves.set_curve_color(color)

    def set_smoothing(
        self, window: int, show_raw: bool = False, use_savgol: bool = False
    ) -> None:
        self._smooth_window = max(0, min(11, window))
        self._show_raw = show_raw and self._smooth_window > 0
        self._smooth_savgol = use_savgol
        self._refresh()

    def set_peaks_visible(self, visible: bool) -> None:
        self._show_peaks = visible
        self._refresh_peaks()

    def set_target_gain_search(
        self, gain_db: Optional[float], fc_hz_list: Optional[list] = None
    ) -> None:
        """Affiche la ligne gain cible et les fréquences d'intersection (recherche personnalisée)."""
        if gain_db is None:
            self._cutoff_viz.set_target_gain(None)
            self._cutoff_viz.set_target_gain_frequencies([])
        else:
            self._cutoff_viz.set_target_gain(gain_db, f"{gain_db:.1f} dB")
            self._cutoff_viz.set_target_gain_frequencies(fc_hz_list or [])

    def set_cutoff_visible(self, visible: bool) -> None:
        self._show_cutoff = visible
        self._refresh_cutoff()

    def _refresh(self) -> None:
        if not self._dataset or self._dataset.is_empty():
            self._curves.clear()
            self._cutoff_viz.set_level(None)
            return
        self._curves.set_data(
            self._dataset,
            y_linear=self._y_linear,
            smooth_window=self._smooth_window,
            show_raw=self._show_raw,
            smooth_savgol_flag=self._smooth_savgol,
        )
        self._refresh_cutoff()
        self._refresh_peaks()
        self._cutoff_viz.update_label_position()

    def _refresh_cutoff(self) -> None:
        if not self._show_cutoff or not self._dataset or self._dataset.is_empty():
            self._cutoff_viz.set_level(None)
            self._cutoff_viz.set_cutoff_frequencies([])
            return
        level = LEVEL_LINEAR if self._y_linear else LEVEL_DB
        self._cutoff_viz.set_level(level)
        # Marqueurs des fréquences de coupure -3 dB (en espace dB)
        finder = Cutoff3DbFinder()
        cutoffs = finder.find_all(self._dataset)
        self._cutoff_viz.set_cutoff_frequencies([r.fc_hz for r in cutoffs])
        self._cutoff_viz.update_label_position()

    def _refresh_peaks(self) -> None:
        """Affiche les marqueurs pics (maxima) et creux (minima) locaux."""
        plot_item = self._plot_widget.getPlotItem()
        if self._peaks_scatter is None:
            self._peaks_scatter = pg.ScatterPlotItem(
                size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 200, 0, 200),
                symbol="o", zValue=8,
            )
            plot_item.addItem(self._peaks_scatter)
        if self._valleys_scatter is None:
            self._valleys_scatter = pg.ScatterPlotItem(
                size=10, pen=pg.mkPen(None), brush=pg.mkBrush(100, 200, 255, 200),
                symbol="o", zValue=8,
            )
            plot_item.addItem(self._valleys_scatter)
        if not self._show_peaks or not self._dataset or self._dataset.is_empty():
            self._peaks_scatter.setData([], [])
            self._valleys_scatter.setData([], [])
            return
        freqs = self._dataset.freqs_hz()
        gains = self._dataset.gains_db()
        peaks_valleys = find_peaks_and_valleys(freqs, gains, order=3)
        px, py = [], []
        vx, vy = [], []
        for f, g_db, kind in peaks_valleys:
            g_show = (10 ** (g_db / 20.0)) if self._y_linear else g_db
            if kind == "pic":
                px.append(f)
                py.append(g_show)
            else:
                vx.append(f)
                vy.append(g_show)
        self._peaks_scatter.setData(px, py)
        self._valleys_scatter.setData(vx, vy)

    def get_data_range(self) -> Optional[Tuple[float, float, float, float]]:
        """Retourne (x_min, x_max, y_min, y_max) des données avec marge, ou None si vide."""
        if not self._dataset or self._dataset.is_empty():
            return None
        freqs = self._dataset.freqs_hz()
        ys = self._dataset.gains_linear() if self._y_linear else self._dataset.gains_db()
        x_min, x_max = min(freqs), max(freqs)
        y_min, y_max = min(ys), max(ys)
        dx = (x_max - x_min) * _AUTO_RANGE_MARGIN or x_min * 0.1
        dy = (y_max - y_min) * _AUTO_RANGE_MARGIN or 1.0
        return (
            max(x_min - dx, 0.1) if x_min > 0 else 0.1,
            x_max + dx,
            y_min - dy,
            y_max + dy,
        )

    def auto_range(self) -> None:
        """Recadre la vue sur les données (avec marge)."""
        r = self.get_data_range()
        if r is not None:
            self.set_view_range(r[0], r[1], r[2], r[3])
        else:
            vb = self._plot_widget.getViewBox()
            vb.enableAutoRange()
            vb.autoRange()

    def set_view_range(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
    ) -> None:
        """Fixer les limites des axes (fréquence en Hz, gain selon unité courante)."""
        logger.debug(
            "Bode plot set_view_range: x_min=%.6g, x_max=%.6g, y_min=%.6g, y_max=%.6g (Hz / gain)",
            x_min, x_max, y_min, y_max,
        )
        vb = self._plot_widget.getViewBox()
        vb.disableAutoRange()
        # En mode log (axe X), la ViewBox pyqtgraph attend la plage en exposants (log10(Hz)),
        # pas en Hz. Sinon elle ignore nos valeurs et garde les limites par défaut (-307.6, 308.2),
        # d'où l'échelle aberrante (10^-300 à 10^300). On convertit Hz → log10(Hz).
        log_mode_x = vb.state.get("logMode", [False, False])[0]
        if log_mode_x:
            x_lo = math.log10(max(float(x_min), 1e-307))
            x_hi = math.log10(min(float(x_max), 1e308))
            vb.setRange(
                xRange=(x_lo, x_hi),
                padding=0,
                update=True,
                disableAutoRange=True,
            )
        else:
            vb.setRange(
                xRange=(float(x_min), float(x_max)),
                padding=0,
                update=True,
                disableAutoRange=True,
            )
        vb.setRange(
            yRange=(float(y_min), float(y_max)),
            padding=0,
            update=True,
            disableAutoRange=True,
        )
        r = vb.viewRange()
        logger.debug(
            "Bode plot après set_view_range: viewRange X=%s, Y=%s",
            r[0], r[1],
        )
        self._cutoff_viz.update_label_position()

    def set_rect_zoom_mode(self, enabled: bool) -> None:
        """True = glisser pour sélectionner une zone et zoomer ; False = glisser pour déplacer (pan)."""
        vb = self._plot_widget.getViewBox()
        vb.setMouseMode(vb.RectMode if enabled else vb.PanMode)

    def get_view_range(self) -> Tuple[float, float, float, float]:
        """Retourne (x_min, x_max, y_min, y_max) en Hz / gain. En mode log (axe X), la ViewBox
        peut renvoyer l'axe X en exposants (ex. -307.6, 308.2) au lieu de Hz ; on convertit en Hz."""
        vb = self._plot_widget.getViewBox()
        r = vb.viewRange()
        x_lo, x_hi = r[0][0], r[0][1]
        y_lo, y_hi = r[1][0], r[1][1]
        # Détecter si l'axe X est en espace log (exposants) : valeurs négatives ou > 400
        if x_lo <= 0 or x_hi <= 0 or x_lo > 500 or x_hi > 500:
            # Interpréter comme log10(f_Hz), convertir en Hz (avec bornes pour éviter overflow)
            exp_lo = max(-307.6, min(308.2, x_lo))
            exp_hi = max(-307.6, min(308.2, x_hi))
            x_lo = 10.0 ** exp_lo
            x_hi = 10.0 ** exp_hi
            if not math.isfinite(x_lo):
                x_lo = 1e-307
            if not math.isfinite(x_hi):
                x_hi = 1e308
            # Si la plage est celle des limites par défaut de la ViewBox (~0 à ~1e308), utiliser la plage des données
            if self._dataset and not self._dataset.is_empty() and (x_hi > 1e200 or x_lo < 1e-200):
                dr = self.get_data_range()
                if dr is not None:
                    x_lo, x_hi = dr[0], dr[1]
                    logger.debug(
                        "Bode plot get_view_range: viewRange X=limites par défaut → plage données x=[%.6g, %.6g], y=[%.6g, %.6g]",
                        x_lo, x_hi, y_lo, y_hi,
                    )
                else:
                    logger.debug(
                        "Bode plot get_view_range: viewRange X en exposants → Hz x=[%.6g, %.6g], y=[%.6g, %.6g] (raw X=%s)",
                        x_lo, x_hi, y_lo, y_hi, r[0],
                    )
            else:
                logger.debug(
                    "Bode plot get_view_range: viewRange X en exposants → Hz x=[%.6g, %.6g], y=[%.6g, %.6g] (raw X=%s)",
                    x_lo, x_hi, y_lo, y_hi, r[0],
                )
        else:
            logger.debug(
                "Bode plot get_view_range: x=[%.6g, %.6g], y=[%.6g, %.6g] (viewRange raw: X=%s, Y=%s)",
                x_lo, x_hi, y_lo, y_hi, r[0], r[1],
            )
        return (x_lo, x_hi, y_lo, y_hi)

    def export_png(self, path: str) -> bool:
        try:
            vb = self._plot_widget.getViewBox()
            vb.setBackgroundColor(_BG_DARK if self._background_dark else _BG_LIGHT)
            exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
            exporter.export(path)
            return True
        except Exception:
            return False
