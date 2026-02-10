"""
Panneau Forme d'onde DOS1102 : récupération :DATA:WAVE:SCREen:HEAD? + SCREEN:CHn? et affichage courbe.
Réutilisable : set_protocol(), set_connected(). Utilise core.dos1102_waveform pour le décodage.
"""
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
    QMessageBox,
    QWidget,
    QDialog,
)

class OscilloscopeWaveformPanel(QWidget):
    """Récupération des données forme d'onde (API Hanmatek/OWON) et affichage courbes CH1/CH2."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._waveform_last: Optional[dict] = None  # {meta, time, ch1, ch2}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        gb = QGroupBox("Forme d'onde")
        v_layout = QVBoxLayout(gb)
        row = QHBoxLayout()
        self._fetch_btn = QPushButton("Récupérer forme d'onde (:DATA:WAVE:SCREEN)")
        self._fetch_btn.setToolTip("HEAD? + CH1? + CH2? (binaire, décodé en volts)")
        self._fetch_btn.clicked.connect(self._on_fetch)
        self._fetch_btn.setEnabled(False)
        row.addWidget(self._fetch_btn)
        self._plot_btn = QPushButton("Afficher courbe")
        self._plot_btn.clicked.connect(self._on_plot)
        self._plot_btn.setEnabled(False)
        self._plot_btn.setToolTip("Affiche temps (s) vs tension CH1/CH2 (V)")
        row.addWidget(self._plot_btn)
        row.addStretch()
        v_layout.addLayout(row)
        self._text = QPlainTextEdit()
        self._text.setPlaceholderText(
            "Résumé méta + nombre de points — « Afficher courbe » trace CH1 et CH2"
        )
        self._text.setMaximumHeight(120)
        self._text.setReadOnly(True)
        v_layout.addWidget(self._text)
        layout.addWidget(gb)

    def set_protocol(self, protocol: Optional[Any]) -> None:
        self._protocol = protocol

    def set_connected(self, connected: bool) -> None:
        self._fetch_btn.setEnabled(connected)
        if not connected:
            self._plot_btn.setEnabled(False)
            self._waveform_last = None

    def _on_fetch(self) -> None:
        if not self._protocol:
            return
        try:
            result = self._protocol.get_waveform_screen()
            self._waveform_last = result
            meta = result["meta"]
            time_arr = result.get("time", [])
            ch1_arr = result.get("ch1", [])
            ch2_arr = result.get("ch2", [])
            n = len(time_arr)
            sample = meta.get("SAMPLE", {})
            sr = sample.get("SAMPLERATE", "?")
            lines = [f"Méta : {n} points, sample rate {sr}"]
            if ch1_arr:
                lines.append(f"CH1 min/max : {min(ch1_arr):.4f} V / {max(ch1_arr):.4f} V")
            if ch2_arr:
                lines.append(f"CH2 min/max : {min(ch2_arr):.4f} V / {max(ch2_arr):.4f} V")
            # Si les deux canaux sont plats à 0 V, rappeler le couplage GND
            if ch1_arr and ch2_arr:
                m1, M1 = min(ch1_arr), max(ch1_arr)
                m2, M2 = min(ch2_arr), max(ch2_arr)
                if abs(M1 - m1) < 1e-9 and abs(M2 - m2) < 1e-9 and abs(m1) < 1e-9 and abs(m2) < 1e-9:
                    lines.append("")
                    lines.append("Les deux voies sont à 0 V (trait continu). Si les sondes sont branchées, passez le couplage en DC (ou AC) dans le panneau Canaux puis « Appliquer canaux ».")
            self._text.setPlainText("\n".join(lines))
            self._plot_btn.setEnabled(n > 0)
        except Exception as e:
            self._text.setPlainText(f"Erreur : {e}")
            self._waveform_last = None
            self._plot_btn.setEnabled(False)

    def _on_plot(self) -> None:
        if not self._waveform_last:
            return
        try:
            import pyqtgraph as pg
            from PyQt6.QtWidgets import QVBoxLayout
        except ImportError:
            QMessageBox.warning(
                self, "Forme d'onde",
                "pyqtgraph requis. Installez : pip install pyqtgraph",
            )
            return
        time_arr = self._waveform_last["time"]
        ch1 = self._waveform_last["ch1"]
        ch2 = self._waveform_last["ch2"]
        if not time_arr or len(time_arr) != len(ch1):
            QMessageBox.information(
                self, "Forme d'onde",
                "Données insuffisantes pour le tracé.",
            )
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Courbe forme d'onde")
        layout = QVBoxLayout(dlg)
        pw = pg.PlotWidget()
        pw.setLabel("bottom", "Temps (s)")
        pw.setLabel("left", "Tension (V)")
        pw.plot(time_arr, ch1, pen="y", name="CH1")
        pw.plot(time_arr, ch2, pen="c", name="CH2")
        pw.addLegend()
        layout.addWidget(pw)
        dlg.resize(600, 400)
        dlg.exec()
