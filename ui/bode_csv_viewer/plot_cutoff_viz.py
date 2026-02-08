"""
Affichage de la ligne horizontale à -3 dB et des marqueurs de fréquences de coupure.
Convient à tous les types de filtres (passe-bas, coupe-bande, etc.).
"""
from typing import Any, List, Optional

import pyqtgraph as pg
from PyQt6.QtCore import Qt

# Niveau -3 dB en gain linéaire (Us/Ue)
LEVEL_DB = -3.0
LEVEL_LINEAR = 10 ** (LEVEL_DB / 20.0)

# Style des lignes verticales fc
PEN_FC = pg.mkPen("#ff8080", width=1.5, style=Qt.PenStyle.DotLine)
# Ligne et marqueurs gain cible (recherche personnalisée)
PEN_TARGET = pg.mkPen("#60c0ff", width=1.5, style=Qt.PenStyle.DashLine)
PEN_TARGET_FC = pg.mkPen("#80b0ff", width=1, style=Qt.PenStyle.DotLine)


def _format_freq(hz: float) -> str:
    """Ex. 1234.5 -> '1,23 kHz', 0.05 -> '50 Hz'."""
    if hz >= 1000:
        return f"{hz / 1000:.2f} kHz"
    if hz < 1 and hz > 0:
        return f"{hz * 1000:.1f} mHz"
    return f"{hz:.1f} Hz"


class CutoffMarkerViz:
    """Ligne horizontale rouge à -3 dB (gain) avec étiquette + marqueurs fc optionnels."""
    PEN = pg.mkPen("#ff6060", width=2.5, style=Qt.PenStyle.DashLine)
    Z_LINE = 10
    Z_LABEL = 11
    Z_FC = 9

    def __init__(self, plot_item: Any):
        self._plot_item = plot_item
        self._line: Optional[Any] = None
        self._label: Optional[Any] = None
        self._y_level: Optional[float] = None
        self._fc_lines: List[Any] = []
        self._fc_labels: List[Any] = []
        # Gain cible (recherche personnalisée)
        self._target_line: Optional[Any] = None
        self._target_label: Optional[Any] = None
        self._target_y: Optional[float] = None
        self._target_fc_lines: List[Any] = []
        self._target_fc_labels: List[Any] = []

    def set_level(self, y_value: Optional[float]) -> None:
        """
        Affiche une ligne horizontale au niveau gain donné.
        y_value: en dB (-3) ou en linéaire (Us/Ue) selon l'axe Y. None = masquer.
        """
        self._y_level = y_value
        if self._line is None:
            self._line = pg.InfiniteLine(
                pos=LEVEL_DB, angle=0, movable=False, pen=self.PEN,
            )
            self._line.setZValue(self.Z_LINE)
            self._plot_item.addItem(self._line)
        if self._label is None:
            self._label = pg.TextItem(anchor=(1, 0.5), text="-3 dB")
            self._label.setColor("#ff5050")
            self._label.setZValue(self.Z_LABEL)
            self._plot_item.addItem(self._label)
        if y_value is not None:
            self._line.setPos(y_value)
            self._line.setVisible(True)
            self._label.setVisible(True)
            self.update_label_position()
        else:
            self._line.setVisible(False)
            self._label.setVisible(False)

    def set_cutoff_frequencies(self, fc_hz_list: List[float]) -> None:
        """
        Affiche des lignes verticales et étiquettes aux fréquences de coupure -3 dB.
        fc_hz_list: liste des fréquences en Hz (vide = masquer les marqueurs).
        """
        for item in self._fc_lines + self._fc_labels:
            self._plot_item.removeItem(item)
        self._fc_lines.clear()
        self._fc_labels.clear()
        for k, fc_hz in enumerate(fc_hz_list):
            line = pg.InfiniteLine(pos=fc_hz, angle=90, movable=False, pen=PEN_FC)
            line.setZValue(self.Z_FC)
            self._plot_item.addItem(line)
            self._fc_lines.append(line)
            label_text = f"fc = {_format_freq(fc_hz)}" if len(fc_hz_list) == 1 else f"fc{k + 1} = {_format_freq(fc_hz)}"
            label = pg.TextItem(anchor=(0, 0.5), text=label_text)
            label.setColor("#ff8080")
            label.setZValue(self.Z_LABEL)
            label.setPos(fc_hz, self._y_level if self._y_level is not None else LEVEL_DB)
            self._plot_item.addItem(label)
            self._fc_labels.append(label)

    def set_target_gain(self, gain_db: Optional[float], label: str = "") -> None:
        """Affiche une ligne horizontale au gain cible (recherche personnalisée). gain_db=None masque."""
        self._target_y = gain_db
        if self._target_line is None:
            self._target_line = pg.InfiniteLine(pos=0, angle=0, movable=False, pen=PEN_TARGET)
            self._target_line.setZValue(self.Z_LINE - 1)
            self._plot_item.addItem(self._target_line)
        if self._target_label is None:
            self._target_label = pg.TextItem(anchor=(1, 0.5), text="")
            self._target_label.setColor("#60b0ff")
            self._target_label.setZValue(self.Z_LABEL)
            self._plot_item.addItem(self._target_label)
        if gain_db is not None:
            self._target_line.setPos(gain_db)
            self._target_line.setVisible(True)
            self._target_label.setText(label or f"{gain_db:.1f} dB")
            self._target_label.setVisible(True)
            vb = self._plot_item.getViewBox()
            if vb:
                x_max = vb.viewRange()[0][1]
                self._target_label.setPos(x_max, gain_db)
        else:
            self._target_line.setVisible(False)
            self._target_label.setVisible(False)

    def set_target_gain_frequencies(self, fc_hz_list: List[float]) -> None:
        """Marqueurs verticaux aux fréquences où la courbe coupe le gain cible."""
        for item in self._target_fc_lines + self._target_fc_labels:
            self._plot_item.removeItem(item)
        self._target_fc_lines.clear()
        self._target_fc_labels.clear()
        y_ref = self._target_y if self._target_y is not None else 0
        for k, fc_hz in enumerate(fc_hz_list):
            line = pg.InfiniteLine(pos=fc_hz, angle=90, movable=False, pen=PEN_TARGET_FC)
            line.setZValue(self.Z_FC - 1)
            self._plot_item.addItem(line)
            self._target_fc_lines.append(line)
            lbl = pg.TextItem(anchor=(0, 0.5), text=f"f = {_format_freq(fc_hz)}")
            lbl.setColor("#80b0ff")
            lbl.setZValue(self.Z_LABEL)
            lbl.setPos(fc_hz, y_ref)
            self._plot_item.addItem(lbl)
            self._target_fc_labels.append(lbl)

    def update_label_position(self) -> None:
        if self._y_level is None or self._label is None or not self._label.isVisible():
            return
        vb = self._plot_item.getViewBox()
        if vb:
            x_min, x_max = vb.viewRange()[0]
            self._label.setPos(x_max, self._y_level)
        if self._target_y is not None and self._target_label and self._target_label.isVisible() and vb:
            self._target_label.setPos(vb.viewRange()[0][1], self._target_y)
