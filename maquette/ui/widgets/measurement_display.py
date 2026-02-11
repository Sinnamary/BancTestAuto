"""
Widget d'affichage principal type LCD : valeur + unité, option affichage secondaire (Hz).
Réutilisable par meter_view et logging_view.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGroupBox, QLabel, QCheckBox
from PyQt6.QtCore import pyqtSignal


class MeasurementDisplay(QWidget):
    """Affichage valeur + unité (style LCD) et option fréquence secondaire (Hz)."""

    secondary_display_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        display_gb = QGroupBox("Affichage")
        display_layout = QHBoxLayout(display_gb)
        self._value_label = QLabel("—")
        self._value_label.setStyleSheet(
            "font-size: 28px; font-family: Consolas, monospace;"
        )
        self._value_label.setMinimumWidth(200)
        display_layout.addWidget(self._value_label)
        display_layout.addStretch()
        self._secondary_check = QCheckBox("Afficher Hz")
        self._secondary_check.toggled.connect(self.secondary_display_toggled.emit)
        display_layout.addWidget(self._secondary_check)
        self._secondary_label = QLabel("—")
        self._secondary_label.setStyleSheet("font-size: 14px;")
        display_layout.addWidget(self._secondary_label)
        layout.addWidget(display_gb)

    def set_value(self, text: str) -> None:
        """Affiche la valeur principale (ex. « 12.345 V » ou « — »)."""
        self._value_label.setText(text)

    def set_secondary(self, text: str) -> None:
        """Affiche la valeur secondaire (ex. fréquence Hz)."""
        self._secondary_label.setText(text)

    def is_secondary_visible(self) -> bool:
        """Retourne True si « Afficher Hz » est coché."""
        return self._secondary_check.isChecked()

    def set_secondary_visible(self, checked: bool) -> None:
        """Coche ou décoche « Afficher Hz » sans émettre le signal."""
        self._secondary_check.blockSignals(True)
        self._secondary_check.setChecked(checked)
        self._secondary_check.blockSignals(False)
