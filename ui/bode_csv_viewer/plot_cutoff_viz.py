"""
Affichage du marqueur de fréquence de coupure -3 dB. Autonome viewer CSV.
"""
from typing import Any, Optional

import pyqtgraph as pg
from PyQt6.QtCore import Qt


class CutoffMarkerViz:
    """Ligne verticale et étiquette pour fc."""
    PEN = pg.mkPen("#00a0ff", width=1.5, style=Qt.PenStyle.DashLine)
    Z_LINE = 10
    Z_LABEL = 11

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._line: Optional[Any] = None
        self._label: Optional[Any] = None
        self._fc_hz: Optional[float] = None

    def set_fc(self, fc_hz: Optional[float]) -> None:
        self._fc_hz = fc_hz
        if self._line is None:
            self._line = pg.InfiniteLine(
                pos=0, angle=90, movable=False, pen=self.PEN,
            )
            self._line.setZValue(self.Z_LINE)
            self._plot_item.addItem(self._line)
        if self._label is None:
            self._label = pg.TextItem(anchor=(0, 1))
            self._label.setZValue(self.Z_LABEL)
            self._plot_item.addItem(self._label)
        if fc_hz is not None and fc_hz > 0:
            self._line.setPos(fc_hz)
            self._line.setVisible(True)
            text = f"fc = {fc_hz/1000:.2f} kHz" if fc_hz >= 1000 else f"fc = {fc_hz:.1f} Hz"
            self._label.setText(text)
            vb = self._plot_item.getViewBox()
            if vb:
                self._label.setPos(fc_hz, vb.viewRange()[1][1])
            self._label.setVisible(True)
        else:
            self._line.setVisible(False)
            self._label.setVisible(False)

    def update_label_position(self) -> None:
        if self._fc_hz is None or self._label is None or not self._label.isVisible():
            return
        vb = self._plot_item.getViewBox()
        if vb:
            self._label.setPos(self._fc_hz, vb.viewRange()[1][1])
