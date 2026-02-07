"""
Widget graphique Bode : gain (dB) vs fréquence (Hz), axe X en échelle logarithmique.
Réutilisable pour affichage et export image.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg


class BodePlotWidget(QWidget):
    """Courbe de Bode semi-log (X = log(f), Y = gain dB)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._plot = pg.PlotWidget()
        self._plot.setLabel("left", "Gain", units="dB")
        self._plot.setLabel("bottom", "Fréquence", units="Hz")
        self._plot.setLogMode(x=True, y=False)
        self._curve = self._plot.plot(pen=pg.mkPen("y", width=2))
        layout.addWidget(self._plot)
        self._freqs = []
        self._gains_db = []

    def set_data(self, freqs: list[float], gains_db: list[float]) -> None:
        """Met à jour la courbe (listes f en Hz et gain en dB)."""
        self._freqs = list(freqs)
        self._gains_db = list(gains_db)
        self._curve.setData(self._freqs, self._gains_db)

    def set_bode_points(self, points: list) -> None:
        """Accepte une liste de BodePoint (objets avec f_hz et gain_db)."""
        self._freqs = [p.f_hz for p in points]
        self._gains_db = [p.gain_db for p in points]
        self._curve.setData(self._freqs, self._gains_db)

    def clear(self) -> None:
        self._freqs = []
        self._gains_db = []
        self._curve.setData([], [])

    def export_image(self, path: str) -> bool:
        """Exporte le graphique en PNG. Retourne True si succès."""
        try:
            self._plot.getViewBox().setBackgroundColor("k")
            exporter = pg.exporters.ImageExporter(self._plot.plotItem)
            exporter.export(path)
            return True
        except Exception:
            return False
