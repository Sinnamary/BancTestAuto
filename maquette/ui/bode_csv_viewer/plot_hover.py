"""
Affichage des coordonnées (f, G) au survol du graphique Bode.
Module autonome, utilisé par BodeCsvPlotWidget.
"""
import math
from typing import Any, Optional

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import QEvent
import pyqtgraph as pg


def create_hover_label(plot_item: Any) -> pg.TextItem:
    """Crée un TextItem pour afficher f et gain au survol."""
    label = pg.TextItem(anchor=(0, 1), text="")
    label.setZValue(20)
    label.setVisible(False)
    plot_item.addItem(label)
    return label


def scene_pos_to_freq_gain(
    plot_widget: Any,
    scene_pos,
    y_linear: bool,
) -> Optional[tuple]:
    """
    Convertit une position scène en (f_hz, y_value) dans le repère du graphique.
    Retourne None si hors zone ou données invalides.
    """
    vb = plot_widget.getViewBox()
    if not vb.sceneBoundingRect().contains(scene_pos):
        return None
    p = vb.mapSceneToView(scene_pos)
    x_data, y_data = p.x(), p.y()
    log_mode_x = vb.state.get("logMode", [False, False])[0]
    if log_mode_x:
        try:
            f_hz = 10.0 ** float(x_data)
        except (TypeError, ValueError, OverflowError):
            return None
    else:
        f_hz = float(x_data)
    if f_hz <= 0 or not math.isfinite(f_hz):
        return None
    return (f_hz, y_data, y_linear)


def format_hover_text(f_hz: float, y_value: float, y_linear: bool) -> str:
    """Formate le texte affiché au survol."""
    unit = "dB" if not y_linear else "Us/Ue"
    if f_hz >= 1000:
        f_str = f"{f_hz / 1000:.3f} kHz"
    else:
        f_str = f"{f_hz:.2f} Hz"
    return f"f = {f_str}  |  G = {y_value:.2f} {unit}"


def update_hover_from_viewport_event(
    viewport: Any,
    event: QEvent,
    plot_widget: Any,
    hover_label: pg.TextItem,
    y_linear: bool,
) -> None:
    """Met à jour le label de survol à partir d'un événement souris sur le viewport."""
    if event.type() != QEvent.Type.MouseMove:
        return
    view = viewport.parent()
    if not isinstance(view, QGraphicsView):
        return
    pos_in_view = viewport.mapTo(view, event.pos())
    scene_pos = view.mapToScene(pos_in_view)
    update_hover_from_scene_pos(plot_widget, scene_pos, hover_label, y_linear)


def update_hover_from_scene_pos(
    plot_widget: Any,
    scene_pos,
    hover_label: pg.TextItem,
    y_linear: bool,
) -> None:
    """Met à jour le label de survol à partir d'une position scène."""
    if hover_label is None:
        return
    result = scene_pos_to_freq_gain(plot_widget, scene_pos, y_linear)
    if result is None:
        hover_label.setVisible(False)
        return
    f_hz, y_value, _ = result
    hover_label.setText(format_hover_text(f_hz, y_value, y_linear))
    vb = plot_widget.getViewBox()
    if vb.state.get("logMode", [False, False])[0]:
        x_pos = math.log10(max(f_hz, 1e-307))
    else:
        x_pos = f_hz
    hover_label.setPos(x_pos, y_value)
    hover_label.setVisible(True)
