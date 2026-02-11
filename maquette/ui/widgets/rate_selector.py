"""
Sélecteur de vitesse de mesure : Rapide (F), Moyenne (M), Lente (L).
Émet rate_changed("F" | "M" | "L").
"""
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QRadioButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal


class RateSelector(QGroupBox):
    """Rapide / Moyenne / Lente. Émet rate_changed(str)."""

    rate_changed = pyqtSignal(str)  # "F", "M" ou "L"

    def __init__(self, parent=None):
        super().__init__("Vitesse", parent)
        self._group = QButtonGroup(self)
        self._buttons = []  # [(QRadioButton, rate_str), ...]
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        for label, rate in (("Rapide", "F"), ("Moyenne", "M"), ("Lente", "L")):
            rb = QRadioButton(label)
            rb.clicked.connect(lambda checked, r=rate: self.rate_changed.emit(r))
            self._group.addButton(rb)
            layout.addWidget(rb)
            self._buttons.append((rb, rate))
        if self._buttons:
            self._buttons[0][0].setChecked(True)

    def set_rate(self, rate: str) -> None:
        """Sélectionne la vitesse ("F", "M" ou "L") sans émettre le signal."""
        for rb, r in self._buttons:
            if r == rate.upper():
                rb.setChecked(True)
                break

    def current_rate(self) -> str:
        """Valeur actuellement sélectionnée."""
        for rb, r in self._buttons:
            if rb.isChecked():
                return r
        return "F"
