"""
Canvas Bode minimal : PlotWidget + axes + mode log X. Fichier minimal pour le debug.
"""
import pyqtgraph as pg

from core.app_logger import get_logger
from .plot_range import apply_view_range

logger = get_logger(__name__)


def create_bode_canvas():
    """
    Crée un PlotWidget configuré pour Bode (log X, labels, plage par défaut).
    Retourne (plot_widget, plot_item, main_viewbox).
    """
    pw = pg.PlotWidget()
    pw.setLabel("left", "Gain", units="dB")
    pw.setLabel("bottom", "Fréquence", units="Hz")
    pw.setLogMode(x=True, y=False)
    pw.getPlotItem().getAxis("bottom").enableAutoSIPrefix(False)
    vb = pw.getViewBox()
    vb.setMouseMode(vb.PanMode)
    vb.disableAutoRange()
    apply_view_range(vb, 1.0, 1e6, -40.0, 5.0, log_mode_x=True)
    try:
        vb.setAntialiasing(True)
    except Exception:
        pass
    logger.debug("plot_canvas: main_vb id=%s mouseMode=%s", id(vb), vb.state.get("mouseMode"))
    return pw, pw.getPlotItem(), vb
