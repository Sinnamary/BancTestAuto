"""
Widget graphique Bode pour le viewer CSV. Compose grille, courbes, marqueur fc.
Zoom (molette, zoom zone), pan, réglage des échelles. Aucune dépendance au banc de test.
"""
from typing import Optional, Tuple, Union

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg

# Polices pour une bonne lisibilité des échelles (rapport/gain et fréquence)
_AXIS_LABEL_FONT_SIZE = 11
_TICK_LABEL_FONT_SIZE = 10

from .model import BodeCsvDataset
from .plot_grid import BodePlotGrid
from .plot_curves import BodeCurveDrawer
from .plot_cutoff_viz import CutoffMarkerViz, LEVEL_DB, LEVEL_LINEAR

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
        vb = self._plot_widget.getViewBox()
        vb.setMouseMode(vb.PanMode)
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
        self._background_dark = True  # Noir par défaut
        self._apply_axis_fonts()
        self._apply_background_style()

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
            self._cutoff_viz.set_level(None)
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
            self._cutoff_viz.set_level(None)
            return
        level = LEVEL_LINEAR if self._y_linear else LEVEL_DB
        self._cutoff_viz.set_level(level)
        self._cutoff_viz.update_label_position()

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
        vb = self._plot_widget.getViewBox()
        vb.disableAutoRange()
        vb.setXRange(x_min, x_max, padding=0)
        vb.setYRange(y_min, y_max, padding=0)
        self._cutoff_viz.update_label_position()

    def set_rect_zoom_mode(self, enabled: bool) -> None:
        """True = glisser pour sélectionner une zone et zoomer ; False = glisser pour déplacer (pan)."""
        vb = self._plot_widget.getViewBox()
        vb.setMouseMode(vb.RectMode if enabled else vb.PanMode)

    def get_view_range(self) -> Tuple[float, float, float, float]:
        """Retourne (x_min, x_max, y_min, y_max) de la vue actuelle."""
        vb = self._plot_widget.getViewBox()
        r = vb.viewRange()
        return (r[0][0], r[0][1], r[1][0], r[1][1])

    def export_png(self, path: str) -> bool:
        try:
            vb = self._plot_widget.getViewBox()
            vb.setBackgroundColor(_BG_DARK if self._background_dark else _BG_LIGHT)
            exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
            exporter.export(path)
            return True
        except Exception:
            return False
