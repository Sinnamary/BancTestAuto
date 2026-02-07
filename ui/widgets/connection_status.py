"""
Barre de statut de connexion (multimètre + générateur).
Branchée sur les classes série après intégration.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent


class StatusIndicator(QFrame):
    """Pastille verte (connecté) ou rouge (déconnecté)."""
    def __init__(self, connected: bool = True, parent=None):
        super().__init__(parent)
        self._connected = connected
        self.setFixedSize(14, 14)
        self.setStyleSheet("""
            StatusIndicator {
                border-radius: 7px;
                background-color: #2ecc71;
            }
        """ if connected else """
            StatusIndicator {
                border-radius: 7px;
                background-color: #e74c3c;
            }
        """)

    def set_connected(self, connected: bool):
        self._connected = connected
        self.setStyleSheet("""
            StatusIndicator {
                border-radius: 7px;
                background-color: #2ecc71;
            }
        """ if connected else """
            StatusIndicator {
                border-radius: 7px;
                background-color: #e74c3c;
            }
        """)


class ConnectionStatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._multimeter_connected = False
        self._generator_connected = False
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(16)

        self._multimeter_indicator = StatusIndicator(self._multimeter_connected)
        layout.addWidget(self._multimeter_indicator)
        self._multimeter_label = QLabel("Multimètre: Non connecté")
        layout.addWidget(self._multimeter_label)

        sep = QLabel("  |  ")
        sep.setStyleSheet("color: #888;")
        layout.addWidget(sep)

        self._generator_indicator = StatusIndicator(self._generator_connected)
        layout.addWidget(self._generator_indicator)
        self._generator_label = QLabel("Générateur: Non connecté")
        layout.addWidget(self._generator_label)

        layout.addStretch()
        self._params_btn = QPushButton("Paramètres")
        self._params_btn.setObjectName("paramsButton")
        layout.addWidget(self._params_btn)

    def set_multimeter_status(self, connected: bool, model: str = "", port: str = ""):
        self._multimeter_connected = connected
        self._multimeter_indicator.set_connected(connected)
        if connected:
            self._multimeter_label.setText(f"Multimètre: {model or 'XDM'} — {port or '?'}")
        else:
            self._multimeter_label.setText("Multimètre: Non connecté")

    def set_generator_status(self, connected: bool, model: str = "", port: str = ""):
        self._generator_connected = connected
        self._generator_indicator.set_connected(connected)
        if connected:
            self._generator_label.setText(f"Générateur: {model or 'FY6900'} — {port or '?'}")
        else:
            self._generator_label.setText("Générateur: Non connecté")

    def get_params_button(self):
        return self._params_btn
