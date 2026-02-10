"""
Barre de boutons de mode de mesure (maquette).
Copie simplifiée de `ui.widgets.mode_bar.ModeBar` pour garder la même apparence
que l’onglet Multimètre réel, sans aucune dépendance au core.
"""

from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal


# Labels par défaut (ordre identique au projet principal)
DEFAULT_MODE_LABELS = [
    "V⎓",
    "V~",
    "A⎓",
    "A~",
    "Ω",
    "Ω 4W",
    "Hz",
    "s",
    "F",
    "°C",
    "⊿",
    "⚡",
]


class ModeBar(QGroupBox):
    """Barre de boutons de mode avec QButtonGroup. Émet mode_changed(index)."""

    mode_changed = pyqtSignal(int)  # index du mode sélectionné

    def __init__(self, labels=None, parent=None):
        super().__init__("Modes de mesure", parent)
        self._labels = labels or DEFAULT_MODE_LABELS
        self._buttons = []
        self._group = QButtonGroup(self)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(4)
        style = (
            "QPushButton { font-size: 11px; padding: 2px 6px; "
            "min-width: 32px; max-height: 22px; }"
        )
        for i, label in enumerate(self._labels):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(style)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda checked, idx=i: self._emit_mode(idx))
            self._group.addButton(btn)
            layout.addWidget(btn)
            self._buttons.append(btn)
        if self._buttons:
            self._buttons[0].setChecked(True)

    def _emit_mode(self, index: int):
        self.mode_changed.emit(index)

    def set_mode(self, index: int) -> None:
        """Sélectionne le mode par index (sans émettre le signal)."""
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)

    def current_index(self) -> int:
        """Index du bouton actuellement coché."""
        for i, btn in enumerate(self._buttons):
            if btn.isChecked():
                return i
        return 0

