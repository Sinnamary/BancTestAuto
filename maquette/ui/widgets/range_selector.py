"""
Sélecteur de plage (Auto / Manuel + liste déroulante) pour la maquette.
Copie de `ui.widgets.range_selector.RangeSelector`, sans dépendances métier.
"""

from typing import List, Tuple, Any

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QRadioButton, QComboBox
from PyQt6.QtCore import pyqtSignal


class RangeSelector(QGroupBox):
    """Auto / Manuel + QComboBox des plages. Données fournies par set_ranges()."""

    auto_toggled = pyqtSignal(bool)  # True = Auto sélectionné
    range_changed = pyqtSignal(int)  # index de la plage sélectionnée (mode Manuel)

    def __init__(self, parent=None):
        super().__init__("Plage", parent)
        self._range_data: List[Tuple[str, Any]] = []  # [(label, value), ...]
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self._auto_radio = QRadioButton("Auto")
        self._auto_radio.setChecked(True)
        self._auto_radio.toggled.connect(self._on_auto_toggled)
        layout.addWidget(self._auto_radio)
        self._manual_radio = QRadioButton("Manuel")
        self._manual_radio.toggled.connect(self._on_manual_toggled)
        layout.addWidget(self._manual_radio)
        self._combo = QComboBox()
        self._combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self._combo)

    def _on_auto_toggled(self, checked: bool):
        if checked:
            self.auto_toggled.emit(True)
        self._combo.setEnabled(not checked and len(self._range_data) > 0)

    def _on_manual_toggled(self, checked: bool):
        self._combo.setEnabled(checked and len(self._range_data) > 0)
        if checked and self._range_data and self._combo.currentIndex() >= 0:
            self.range_changed.emit(self._combo.currentIndex())

    def _on_combo_changed(self, index: int):
        if index >= 0:
            self.range_changed.emit(index)

    def set_ranges(self, range_data: List[Tuple[str, Any]]) -> None:
        """Met à jour la liste des plages (label affiché, value pour l’appareil)."""
        self._range_data = list(range_data) if range_data else []
        self._combo.blockSignals(True)
        self._combo.clear()
        for label, _ in self._range_data:
            self._combo.addItem(label)
        self._combo.setEnabled(
            not self._auto_radio.isChecked() and len(self._range_data) > 0
        )
        self._combo.blockSignals(False)

    def set_auto(self, auto: bool) -> None:
        """Sélectionne Auto (True) ou Manuel (False) sans émettre de signal."""
        self._auto_radio.blockSignals(True)
        self._manual_radio.blockSignals(True)
        self._auto_radio.setChecked(auto)
        self._manual_radio.setChecked(not auto)
        self._combo.setEnabled(not auto and len(self._range_data) > 0)
        self._auto_radio.blockSignals(False)
        self._manual_radio.blockSignals(False)

    def is_auto(self) -> bool:
        return self._auto_radio.isChecked()

    def current_index(self) -> int:
        return self._combo.currentIndex()

    def get_value_at(self, index: int) -> Any:
        """Valeur associée à l’index (pour envoyer à l’appareil)."""
        if 0 <= index < len(self._range_data):
            return self._range_data[index][1]
        return None

