"""
ViewBox secondaire pour la courbe de phase (axe Y droit). Fichier minimal pour le debug.
Configure le ViewBox phase en log X, courbe phase, et laisse passer la souris (NoButton).
"""
import math
from typing import List

import pyqtgraph as pg
from PyQt6.QtCore import Qt

from core.app_logger import get_logger

logger = get_logger(__name__)


class PhaseOverlay:
    """ViewBox + courbe phase superposés au graphique principal (souris pass-through)."""

    def __init__(self, plot_item, main_viewbox):
        self._plot_item = plot_item
        self._main_vb = main_viewbox
        plot_item.showAxis("right")
        self._right_vb = pg.ViewBox(enableMouse=False)
        self._setup_log_mode()
        plot_item.scene().addItem(self._right_vb)
        self._right_vb.setZValue(10)
        self._make_mouse_passthrough()
        plot_item.getAxis("right").linkToView(self._right_vb)
        self._right_vb.setXLink(self._main_vb)
        self._phase_curve = self._create_phase_curve()
        self._right_vb.addItem(self._phase_curve)
        self._right_vb.setVisible(False)
        plot_item.getAxis("right").setVisible(False)
        plot_item.getAxis("right").setLabel("Phase", units="°")
        self._connect_geometry()

    def _setup_log_mode(self) -> None:
        try:
            if hasattr(self._right_vb, "setLogMode"):
                self._right_vb.setLogMode(0, True)
                self._right_vb.setLogMode(1, False)
            else:
                self._right_vb.state["logMode"] = [True, False]
        except Exception as e:
            logger.warning("PhaseOverlay: setLogMode fallback %s", e)
            self._right_vb.state["logMode"] = [True, False]
        self._right_vb._matrixNeedsUpdate = True
        try:
            self._right_vb.updateMatrix()
        except Exception:
            pass
        logger.debug("PhaseOverlay: right_vb logMode=%s", self._right_vb.state.get("logMode"))

    def _make_mouse_passthrough(self) -> None:
        self._right_vb.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._right_vb.setAcceptHoverEvents(False)
        logger.debug(
            "PhaseOverlay: right_vb acceptedMouseButtons=%s",
            self._right_vb.acceptedMouseButtons(),
        )

    def _create_phase_curve(self) -> pg.PlotDataItem:
        curve = pg.PlotDataItem(pen=pg.mkPen("#40c0c0", width=2), antialias=True)
        if hasattr(curve, "setLogMode"):
            curve.setLogMode(True, False)
        curve.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        curve.setAcceptHoverEvents(False)
        return curve

    def _connect_geometry(self) -> None:
        def sync():
            self._right_vb.setGeometry(self._main_vb.sceneBoundingRect())
            self._right_vb.linkedViewChanged(self._main_vb, self._right_vb.XAxis)
        self._main_vb.sigResized.connect(sync)
        self._main_vb.sigRangeChanged.connect(sync)

    @property
    def right_vb(self):
        return self._right_vb

    @property
    def phase_curve(self):
        return self._phase_curve

    def set_visible(self, visible: bool) -> None:
        self._right_vb.setVisible(visible)
        self._plot_item.getAxis("right").setVisible(visible)
        self._phase_curve.setVisible(visible)

    # z au-dessus du PlotItem (≈0) pour que la phase soit visible quand zoom désactivé
    Z_PHASE_ON_TOP = 10

    def set_zoom_zone_active(self, active: bool) -> None:
        """Zoom désactivé: phase au-dessus (z=10) pour être visible. Zoom activé: phase derrière main (z < main_vb) pour que le main reçoive la souris."""
        main_z = self._main_vb.zValue() if hasattr(self._main_vb, "zValue") else 0
        if active:
            z = main_z - 10
        else:
            z = self.Z_PHASE_ON_TOP
        self._right_vb.setZValue(z)
        logger.debug(
            "PhaseOverlay.set_zoom_zone_active: active=%s → right_vb.setZValue(%s) (main_vb.zValue=%s)",
            active, z, main_z,
        )

    def set_phase_data(self, freqs: List[float], phases_deg: List[float]) -> None:
        self._phase_curve.setData(freqs, phases_deg)
        x_range = list(self._main_vb.viewRange()[0])
        ys = [p if p is not None else 0.0 for p in phases_deg]
        y_finite = [y for y in ys if math.isfinite(y)]
        y_range = (min(y_finite) - 5, max(y_finite) + 5) if y_finite else (-90.0, 0.0)
        self._right_vb.setRange(xRange=tuple(x_range), yRange=y_range, padding=0, update=True, disableAutoRange=True)
        self._right_vb._matrixNeedsUpdate = True
        try:
            self._right_vb.updateMatrix()
        except Exception:
            pass
        self._right_vb.setGeometry(self._main_vb.sceneBoundingRect())
        self._right_vb.linkedViewChanged(self._main_vb, self._right_vb.XAxis)

    def clear_phase_data(self) -> None:
        self._phase_curve.setData([], [])
        self.set_visible(False)
