"""
Dialogue de configuration série (port, débit, timeouts).
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
)


class SerialConfigDialog(QDialog):
    def __init__(self, title: str = "Configuration série", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Port", QComboBox())
        form.addRow("Débit (bauds)", QComboBox())
        form.addRow("Timeout lecture (s)", QDoubleSpinBox())
        form.addRow("Timeout écriture (s)", QDoubleSpinBox())
        form.addRow("Logger les échanges", QCheckBox())
        layout.addLayout(form)
        layout.addWidget(QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        ))
