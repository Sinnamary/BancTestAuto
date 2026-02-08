"""
Widget graphique Bode : gain vs fréquence (Hz), axe X en échelle logarithmique.
Axe Y : gain linéaire (Us/Ue) ou gain en dB, au choix.
Quadrillage, lissage, points significatifs (fc -3 dB), export image.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg

try:
    from core.bode_utils import moving_average_smooth, find_cutoff_3db
except ImportError:
    def moving_average_smooth(values, window):
        return list(values)
    def find_cutoff_3db(freqs, gains_db, gain_ref=None):
        return None


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
        self._plot.showGrid(x=True, y=True, alpha=0.35)
        self._curve = self._plot.plot(pen=pg.mkPen("#e0c040", width=2))
        self._raw_curve = self._plot.plot(pen=pg.mkPen("#808080", width=1, style=Qt.PenStyle.DotLine))
        self._raw_curve.setVisible(False)
        layout.addWidget(self._plot)
        self._points: list = []
        self._y_linear = False
        self._show_grid = True
        self._smooth_window = 0  # 0 = pas de lissage, sinon 3, 5, 7, 9, 11
        self._show_raw_with_smooth = False
        self._cutoff_fc: float | None = None
        self._cutoff_line: pg.InfiniteLine | None = None
        self._cutoff_label: pg.TextItem | None = None
        self._plot.scene().sigMouseClicked.connect(self._on_plot_clicked)

    def _update_axis_label(self) -> None:
        if self._y_linear:
            self._plot.setLabel("left", "Gain (Us/Ue)", units="")
        else:
            self._plot.setLabel("left", "Gain", units="dB")

    def set_show_grid(self, show: bool) -> None:
        self._show_grid = show
        self._plot.showGrid(x=show, y=show, alpha=0.35)

    def set_smoothing(self, window: int, show_raw_curve: bool = False) -> None:
        """window: 0 = désactivé, 3 à 11 = moyenne glissante."""
        self._smooth_window = max(0, min(11, window))
        self._show_raw_with_smooth = show_raw_curve and self._smooth_window > 0
        self._raw_curve.setVisible(self._show_raw_with_smooth and bool(self._points))
        self._refresh_curve()

    def set_cutoff_fc(self, fc_hz: float | None) -> None:
        """Affiche ou masque la ligne verticale et l'étiquette fc."""
        self._cutoff_fc = fc_hz
        if self._cutoff_line is None:
            self._cutoff_line = pg.InfiniteLine(
                pos=0, angle=90, movable=False,
                pen=pg.mkPen("#00a0ff", width=1.5, style=Qt.PenStyle.DashLine),
            )
            self._cutoff_line.setZValue(10)
            self._plot.addItem(self._cutoff_line)
        if self._cutoff_label is None:
            self._cutoff_label = pg.TextItem(anchor=(0, 1))
            self._cutoff_label.setZValue(11)
            self._plot.addItem(self._cutoff_label)
        if fc_hz is not None and fc_hz > 0:
            self._cutoff_line.setPos(fc_hz)
            self._cutoff_line.setVisible(True)
            if fc_hz >= 1000:
                label = f"fc = {fc_hz/1000:.2f} kHz"
            else:
                label = f"fc = {fc_hz:.1f} Hz"
            self._cutoff_label.setText(label)
            self._cutoff_label.setPos(fc_hz, self._plot.getViewBox().viewRange()[1][1])
            self._cutoff_label.setVisible(True)
        else:
            self._cutoff_line.setVisible(False)
            self._cutoff_label.setVisible(False)

    def _on_plot_clicked(self, event) -> None:
        """Optionnel : clic sur le graphique (pour infobulle future)."""
        pass

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
            self._raw_curve.setData([], [])
            self._raw_curve.setVisible(False)
            return
        freqs = [p.f_hz for p in self._points]
        ys_raw = [p.gain_linear for p in self._points] if self._y_linear else [p.gain_db for p in self._points]
        if self._show_raw_with_smooth and self._smooth_window > 0:
            self._raw_curve.setData(freqs, ys_raw)
            self._raw_curve.setVisible(True)
        else:
            self._raw_curve.setData([], [])
            self._raw_curve.setVisible(False)
        if self._smooth_window > 0:
            ys = moving_average_smooth(ys_raw, self._smooth_window)
            self._curve.setData(freqs, ys)
        else:
            self._curve.setData(freqs, ys_raw)
        if self._cutoff_fc is not None and self._cutoff_label is not None and self._cutoff_label.isVisible():
            vb = self._plot.getViewBox()
            if vb:
                self._cutoff_label.setPos(self._cutoff_fc, vb.viewRange()[1][1])

    def clear(self) -> None:
        self._points = []
        self._curve.setData([], [])
        self._raw_curve.setData([], [])
        self._raw_curve.setVisible(False)
        self.set_cutoff_fc(None)

    def auto_range(self) -> None:
        """Recadre la vue sur toutes les données."""
        if not self._points:
            return
        vb = self._plot.getViewBox()
        vb.enableAutoRange()
        vb.autoRange()

    def export_image(self, path: str) -> bool:
        """Exporte le graphique en PNG. Retourne True si succès."""
        try:
            self._plot.getViewBox().setBackgroundColor("k")
            exporter = pg.exporters.ImageExporter(self._plot.plotItem)
            exporter.export(path)
            return True
        except Exception:
            return False

    def get_cutoff_3db(self) -> tuple[float, float] | None:
        """Retourne (fc_hz, gain_db) pour la coupure -3 dB si détectable."""
        if not self._points:
            return None
        freqs = [p.f_hz for p in self._points]
        gains_db = [p.gain_db for p in self._points]
        return find_cutoff_3db(freqs, gains_db)
