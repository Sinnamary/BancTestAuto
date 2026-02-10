"""
Panneau paramètres avancés (RTD, continuité, buzzer) pour la maquette.
Copie de `ui.widgets.advanced_params.AdvancedParamsPanel`.
"""

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import pyqtSignal


class AdvancedParamsPanel(QGroupBox):
    """Température RTD, continuité (seuil), buzzer."""

    rtd_type_changed = pyqtSignal(str)  # KITS90, PT100
    rtd_unit_changed = pyqtSignal(str)  # C, F, K
    rtd_show_changed = pyqtSignal(str)  # TEMP, MEAS, ALL
    continuity_threshold_changed = pyqtSignal(float)
    buzzer_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("Paramètres avancés", parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Température RTD:"))
        row1 = QHBoxLayout()
        self._rtd_type = QComboBox()
        self._rtd_type.addItems(["KITS90", "PT100"])
        self._rtd_type.currentTextChanged.connect(self.rtd_type_changed.emit)
        row1.addWidget(self._rtd_type)
        self._rtd_unit = QComboBox()
        self._rtd_unit.addItems(["°C", "°F", "K"])
        self._rtd_unit.currentTextChanged.connect(self._on_rtd_unit_text)
        row1.addWidget(self._rtd_unit)
        self._rtd_show = QComboBox()
        self._rtd_show.addItems(["TEMP", "MEAS", "ALL"])
        self._rtd_show.currentTextChanged.connect(self.rtd_show_changed.emit)
        row1.addWidget(self._rtd_show)
        layout.addLayout(row1)

        layout.addWidget(QLabel("Continuité seuil (Ω):"))
        self._cont_spin = QDoubleSpinBox()
        self._cont_spin.setRange(0.1, 10000)
        self._cont_spin.setValue(10)
        self._cont_spin.valueChanged.connect(self.continuity_threshold_changed.emit)
        layout.addWidget(self._cont_spin)

        self._buzzer = QCheckBox("Buzzer ON")
        self._buzzer.toggled.connect(self.buzzer_toggled.emit)
        layout.addWidget(self._buzzer)

    def _on_rtd_unit_text(self, text: str):
        u = "C"
        if text and "F" in text.upper():
            u = "F"
        elif text and "K" in text.upper():
            u = "K"
        self.rtd_unit_changed.emit(u)

