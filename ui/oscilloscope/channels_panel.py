"""
Panneau Canaux DOS1102 (couplage CH1 / CH2).
Réutilisable : set_protocol(), set_connected().
"""
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class OscilloscopeChannelsPanel(QWidget):
    """Couplage Voie 1 / Voie 2 (DC, AC, GND)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        gb = QGroupBox("Canaux")
        ch_layout = QVBoxLayout(gb)
        row = QHBoxLayout()
        row.setSpacing(16)

        v1 = QGroupBox("Voie 1")
        v1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        f1 = QFormLayout(v1)
        self._ch1_coup = QComboBox()
        self._ch1_coup.addItems(["DC", "AC", "GND"])
        f1.addRow(QLabel("Couplage:"), self._ch1_coup)
        row.addWidget(v1)

        v2 = QGroupBox("Voie 2")
        v2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        f2 = QFormLayout(v2)
        self._ch2_coup = QComboBox()
        self._ch2_coup.addItems(["DC", "AC", "GND"])
        f2.addRow(QLabel("Couplage:"), self._ch2_coup)
        row.addWidget(v2)

        ch_layout.addLayout(row)
        btn_row = QHBoxLayout()
        self._apply_btn = QPushButton("Appliquer canaux")
        self._apply_btn.clicked.connect(self._on_apply)
        self._apply_btn.setEnabled(False)
        btn_row.addWidget(self._apply_btn)
        btn_row.addStretch()
        ch_layout.addLayout(btn_row)
        layout.addWidget(gb)

    def set_protocol(self, protocol: Optional[Any]) -> None:
        self._protocol = protocol

    def set_connected(self, connected: bool) -> None:
        self._apply_btn.setEnabled(connected)

    def _on_apply(self) -> None:
        if not self._protocol:
            return
        try:
            self._protocol.set_ch1_coupling(self._ch1_coup.currentText())
            self._protocol.set_ch2_coupling(self._ch2_coup.currentText())
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")
