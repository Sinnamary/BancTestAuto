"""
Panneau Acquisition et Trigger DOS1102.

Version alignée sur la maquette : groupbox « Acquisition » (mode + base de temps)
et groupbox « Trigger » (type, source, niveau). La logique de communication reste
gérée par le protocole reçu via set_protocol().
"""
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QWidget,
    QFormLayout,
    QDoubleSpinBox,
)


class OscilloscopeAcqTriggerPanel(QWidget):
    """Acquisition (SAMP / PEAK / AVE) et Trigger (EDGE / VIDEO) + base de temps."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Acquisition ---
        acq_gb = QGroupBox("Acquisition")
        acq_layout = QFormLayout(acq_gb)
        self._acq_combo = QComboBox()
        self._acq_combo.addItems(
            [
                "SAMP (échantillonnage)",
                "PEAK (pic)",
                "AVE (moyenne)",
            ]
        )
        acq_layout.addRow("Mode :", self._acq_combo)

        self._timebase_spin = QDoubleSpinBox()
        self._timebase_spin.setDecimals(6)
        self._timebase_spin.setMinimum(1e-9)
        self._timebase_spin.setMaximum(1000.0)
        self._timebase_spin.setValue(1e-3)
        self._timebase_spin.setSuffix(" s/div")
        acq_layout.addRow("Base de temps :", self._timebase_spin)

        self._acq_btn = QPushButton("Appliquer acquisition")
        self._acq_btn.clicked.connect(self._on_acq_apply)
        self._acq_btn.setEnabled(False)
        acq_layout.addRow("", self._acq_btn)
        layout.addWidget(acq_gb)

        # --- Trigger ---
        trig_gb = QGroupBox("Trigger")
        trig_layout = QFormLayout(trig_gb)

        self._trig_type_combo = QComboBox()
        self._trig_type_combo.addItems(["EDGE", "VIDEO"])
        trig_layout.addRow("Type :", self._trig_type_combo)

        self._trig_source_combo = QComboBox()
        self._trig_source_combo.addItems(["CH1", "CH2", "Ext", "Line"])
        trig_layout.addRow("Source :", self._trig_source_combo)

        self._trig_level_spin = QDoubleSpinBox()
        self._trig_level_spin.setSuffix(" V")
        self._trig_level_spin.setRange(-1000.0, 1000.0)
        self._trig_level_spin.setSingleStep(0.1)
        trig_layout.addRow("Niveau :", self._trig_level_spin)

        self._trig_apply_btn = QPushButton("Appliquer trigger")
        self._trig_apply_btn.setEnabled(False)
        self._trig_apply_btn.clicked.connect(self._on_trig_apply)
        trig_layout.addRow("", self._trig_apply_btn)

        layout.addWidget(trig_gb)

    def set_protocol(self, protocol: Optional[Any]) -> None:
        self._protocol = protocol

    def set_connected(self, connected: bool) -> None:
        self._acq_btn.setEnabled(connected)
        self._trig_apply_btn.setEnabled(connected)

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

            # On applique aussi la base de temps si le protocole le permet.
            if hasattr(self._protocol, "set_hor_scale"):
                self._protocol.set_hor_scale(self._timebase_spin.value())
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")

    def _on_trig_apply(self) -> None:
        if not self._protocol:
            return
        try:
            trig_type = self._trig_type_combo.currentText()
            if trig_type == "EDGE" and hasattr(self._protocol, "set_trig_edge"):
                self._protocol.set_trig_edge()
            elif trig_type == "VIDEO" and hasattr(self._protocol, "set_trig_video"):
                self._protocol.set_trig_video()
            # La gestion fine de la source et du niveau de trigger
            # pourra être ajoutée quand les méthodes existeront dans le protocole.
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")
