"""
Panneau Forme d'onde DOS1102 : récupération :WAV:DATA:ALL? et affichage courbe.
Réutilisable : set_protocol(), set_connected(). Utilise core.dos1102_waveform pour le parsing.
"""
from typing import Any, Optional, Union

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
    QMessageBox,
    QWidget,
)

from core.dos1102_waveform import parse_ascii_waveform, waveform_display_summary


class OscilloscopeWaveformPanel(QWidget):
    """Récupération des données forme d'onde et affichage courbe (si ASCII)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._waveform_last_data: Union[str, bytes, None] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        gb = QGroupBox("Forme d'onde")
        v_layout = QVBoxLayout(gb)
        row = QHBoxLayout()
        self._fetch_btn = QPushButton("Récupérer forme d'onde (:WAV:DATA:ALL?)")
        self._fetch_btn.clicked.connect(self._on_fetch)
        self._fetch_btn.setEnabled(False)
        row.addWidget(self._fetch_btn)
        self._plot_btn = QPushButton("Afficher courbe")
        self._plot_btn.clicked.connect(self._on_plot)
        self._plot_btn.setEnabled(False)
        self._plot_btn.setToolTip("Parse les données et affiche si format reconnu (ASCII nombres)")
        row.addWidget(self._plot_btn)
        row.addStretch()
        v_layout.addLayout(row)
        self._text = QPlainTextEdit()
        self._text.setPlaceholderText(
            "Données brutes (ASCII ou binaire) — « Afficher courbe » tente un tracé"
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
            self._waveform_last_data = None

    def _on_fetch(self) -> None:
        if not self._protocol:
            return
        try:
            raw = self._protocol.waveform_data_raw()
            self._waveform_last_data = raw
            self._text.setPlainText(waveform_display_summary(raw))
            self._plot_btn.setEnabled(bool(raw))
        except Exception as e:
            self._text.setPlainText(f"Erreur : {e}")
            self._waveform_last_data = None
            self._plot_btn.setEnabled(False)

    def _on_plot(self) -> None:
        if not self._waveform_last_data:
            return
        data = self._waveform_last_data
        values = parse_ascii_waveform(data)
        if not values:
            if isinstance(data, bytes):
                QMessageBox.information(
                    self, "Forme d'onde",
                    "Données binaires : affichage courbe non pris en charge (parser selon manuel DSO).",
                )
            else:
                QMessageBox.information(
                    self, "Forme d'onde",
                    "Aucun nombre reconnu. Format attendu : liste de valeurs (virgules ou espaces).",
                )
            return
        try:
            import pyqtgraph as pg
            from PyQt6.QtWidgets import QDialog, QVBoxLayout
        except ImportError:
            QMessageBox.warning(
                self, "Forme d'onde",
                "pyqtgraph requis. Installez : pip install pyqtgraph",
            )
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Courbe forme d'onde")
        layout = QVBoxLayout(dlg)
        pw = pg.PlotWidget()
        pw.setLabel("bottom", "Échantillon")
        pw.setLabel("left", "Valeur")
        x = list(range(len(values)))
        pw.plot(x, values, pen="y")
        layout.addWidget(pw)
        dlg.resize(600, 400)
        dlg.exec()
