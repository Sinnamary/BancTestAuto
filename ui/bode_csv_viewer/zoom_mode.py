"""
Contrôle du mode souris du ViewBox principal : zoom sur zone (RectMode) ou pan (PanMode).
Fichier minimal pour faciliter le debug du zoom.
"""
from core.app_logger import get_logger

logger = get_logger(__name__)


class ZoomModeController:
    """Applique RectMode ou PanMode sur un ViewBox pyqtgraph."""

    def __init__(self, main_viewbox):
        self._vb = main_viewbox
        self._rect_zoom_enabled = False
        logger.debug(
            "ZoomModeController: init main_vb id=%s mouseMode=%s",
            id(self._vb), self._vb.state.get("mouseMode"),
        )

    def set_rect_zoom_enabled(self, enabled: bool) -> None:
        """Active (True) ou désactive (False) le zoom sur zone (glisser)."""
        mode_avant = self._vb.state.get("mouseMode", "?")
        mode = self._vb.RectMode if enabled else self._vb.PanMode
        mode_name = "RectMode" if enabled else "PanMode"
        logger.debug(
            "ZoomModeController.set_rect_zoom_enabled: enabled=%s → %s (valeur=%s), avant=%s",
            enabled, mode_name, mode, mode_avant,
        )
        self._vb.setMouseMode(mode)
        self._rect_zoom_enabled = enabled
        mode_apres = self._vb.state.get("mouseMode", "?")
        enable_mouse = getattr(self._vb, "enableMouse", None)
        if callable(enable_mouse):
            try:
                enable_mouse = enable_mouse()
            except Exception:
                enable_mouse = "?"
        logger.debug(
            "ZoomModeController.set_rect_zoom_enabled: après mouseMode=%s enableMouse=%s",
            mode_apres, enable_mouse,
        )

    def is_rect_zoom_enabled(self) -> bool:
        return self._rect_zoom_enabled

    def get_current_mode(self):
        """Retourne le mode actuel du ViewBox (1=RectMode, 3=PanMode)."""
        return self._vb.state.get("mouseMode")
