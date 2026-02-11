"""
Style du graphique Bode : polices des axes, fond noir/blanc, couleurs des traits.
Centralise les constantes et l'application du thème. Module autonome.
"""
from typing import Any, Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg

AXIS_LABEL_FONT_SIZE = 12
TICK_LABEL_FONT_SIZE = 10
HOVER_FONT_SIZE = 10
HOVER_COLOR_DARK = "#e8e8e8"
HOVER_COLOR_LIGHT = "#1a1a1a"

BG_DARK = "k"
BG_LIGHT = "w"
AXIS_PEN_DARK = pg.mkPen("#c0c0c0")
AXIS_PEN_LIGHT = pg.mkPen("#000000")
TICK_LABEL_COLOR_LIGHT = "#000000"


def _font_family() -> Optional[str]:
    app = QApplication.instance() if QApplication else None
    if app and app.font().family():
        return app.font().family()
    if __import__("sys").platform == "win32":
        return "Segoe UI"
    return None


def apply_axis_fonts(plot_item: Any) -> None:
    """Applique les polices des axes (suit config display.font_family)."""
    family = _font_family()
    label_font = QFont()
    tick_font = QFont()
    if family:
        label_font.setFamily(family)
        tick_font.setFamily(family)
    label_font.setPointSize(AXIS_LABEL_FONT_SIZE)
    label_font.setBold(True)
    tick_font.setPointSize(TICK_LABEL_FONT_SIZE)
    for ax_name in ("left", "bottom"):
        ax_item = plot_item.getAxis(ax_name)
        ax_item.tickFont = tick_font
        if hasattr(ax_item, "label") and ax_item.label is not None:
            ax_item.label.setFont(label_font)
    plot_item.getAxis("left").setWidth(48)
    plot_item.getAxis("bottom").setHeight(42)


def apply_background_style(
    plot_item: Any,
    view_box: Any,
    dark: bool,
    grid: Any,
    hover_label: Optional[Any] = None,
) -> None:
    """
    Applique fond noir ou blanc, couleurs des axes et du quadrillage.
    grid: objet avec set_dark_background(bool).
    hover_label: TextItem optionnel pour (f, G) au survol.
    """
    grid.set_dark_background(dark)
    if dark:
        view_box.setBackgroundColor(BG_DARK)
        _set_axis_pens(plot_item, AXIS_PEN_DARK, QColor("#c0c0c0"))
    else:
        view_box.setBackgroundColor(BG_LIGHT)
        _set_axis_pens(plot_item, AXIS_PEN_LIGHT, QColor(TICK_LABEL_COLOR_LIGHT))
    if hover_label is not None:
        font = QFont()
        family = _font_family()
        if family:
            font.setFamily(family)
        font.setPointSize(HOVER_FONT_SIZE)
        font.setBold(True)
        hover_label.setFont(font)
        hover_label.setColor(
            QColor(HOVER_COLOR_DARK) if dark else QColor(HOVER_COLOR_LIGHT)
        )


def _set_axis_pens(plot_item: Any, pen: Any, text_color: QColor) -> None:
    for ax_name in ("left", "bottom"):
        ax_item = plot_item.getAxis(ax_name)
        ax_item.setPen(pen)
        ax_item.setTextPen(pen)
        if hasattr(ax_item, "label") and ax_item.label is not None:
            ax_item.label.setDefaultTextColor(text_color)
