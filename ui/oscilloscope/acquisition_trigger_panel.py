"""
Panneau Acquisition et Trigger DOS1102.
Réutilisable : reçoit le protocole via set_protocol(), activé via set_connected().
"""
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QWidget,
)


class OscilloscopeAcqTriggerPanel(QWidget):
    """Acquisition (SAMP / PEAK / AVE) et Trigger (EDGE / VIDEO)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        acq_gb = QGroupBox("Acquisition")
        acq_layout = QHBoxLayout(acq_gb)
        acq_layout.addWidget(QLabel("Mode:"))
        self._acq_combo = QComboBox()
        self._acq_combo.addItems(["SAMP (échantillonnage)", "PEAK (pic)", "AVE (moyenne)"])
        acq_layout.addWidget(self._acq_combo)
        self._acq_btn = QPushButton("Appliquer")
        self._acq_btn.clicked.connect(self._on_acq_apply)
        self._acq_btn.setEnabled(False)
        acq_layout.addWidget(self._acq_btn)
        acq_layout.addStretch()
        layout.addWidget(acq_gb)

        trig_gb = QGroupBox("Trigger")
        trig_layout = QHBoxLayout(trig_gb)
        self._trig_edge_btn = QPushButton("EDGE")
        self._trig_edge_btn.clicked.connect(lambda: self._set_trigger("EDGE"))
        self._trig_edge_btn.setEnabled(False)
        self._trig_video_btn = QPushButton("VIDEO")
        self._trig_video_btn.clicked.connect(lambda: self._set_trigger("VIDEO"))
        self._trig_video_btn.setEnabled(False)
        trig_layout.addWidget(self._trig_edge_btn)
        trig_layout.addWidget(self._trig_video_btn)
        trig_layout.addStretch()
        layout.addWidget(trig_gb)

    def set_protocol(self, protocol: Optional[Any]) -> None:
        self._protocol = protocol

    def set_connected(self, connected: bool) -> None:
        self._acq_btn.setEnabled(connected)
        self._trig_edge_btn.setEnabled(connected)
        self._trig_video_btn.setEnabled(connected)

    def _on_acq_apply(self) -> None:
        if not self._protocol:
            return
        try:
            idx = self._acq_combo.currentIndex()
            if idx == 0:
                self._protocol.set_acq_samp()
            elif idx == 1:
                self._protocol.set_acq_peak()
            else:
                self._protocol.set_acq_ave()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")

    def _set_trigger(self, mode: str) -> None:
        if not self._protocol:
            return
        try:
            if mode == "EDGE":
                self._protocol.set_trig_edge()
            else:
                self._protocol.set_trig_video()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")
