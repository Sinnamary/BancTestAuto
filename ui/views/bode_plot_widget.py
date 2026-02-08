"""
Widget graphique Bode : gain vs fréquence (Hz), axe X en échelle logarithmique.
Axe Y : gain linéaire (Us/Ue) ou gain en dB, au choix.
Réutilisable pour affichage et export image.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg


class BodePlotWidget(QWidget):
    """Courbe de Bode semi-log (X = log(f), Y = gain linéaire ou dB)."""

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
        self._points: list = []
        self._y_linear = False

    def _update_axis_label(self) -> None:
        if self._y_linear:
            self._plot.setLabel("left", "Gain (Us/Ue)", units="")
        else:
            self._plot.setLabel("left", "Gain", units="dB")

    def set_data(self, freqs: list[float], gains_db: list[float]) -> None:
        """Met à jour la courbe (listes f en Hz et gain en dB)."""
        self._points = []
        for f, g_db in zip(freqs, gains_db):
            self._points.append(type("P", (), {"f_hz": f, "gain_db": g_db, "gain_linear": 10 ** (g_db / 20.0) if g_db > -200 else 0.0})())
        self._refresh_curve()

    def set_bode_points(self, points: list, y_linear: bool = False) -> None:
        """Accepte une liste de BodePoint. y_linear=True affiche Us/Ue, sinon gain en dB."""
        self._points = list(points)
        self._y_linear = y_linear
        self._update_axis_label()
        self._refresh_curve()

    def _refresh_curve(self) -> None:
        if not self._points:
            self._curve.setData([], [])
            return
        freqs = [p.f_hz for p in self._points]
        ys = [p.gain_linear for p in self._points] if self._y_linear else [p.gain_db for p in self._points]
        self._curve.setData(freqs, ys)

    def clear(self) -> None:
        self._points = []
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
