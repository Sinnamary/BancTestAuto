"""
Barre de statut de connexion (multimètre + générateur).
Branchée sur les classes série après intégration.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QProgressBar,
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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        layout = QHBoxLayout()
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
        self._load_config_btn = QPushButton("Charger config")
        self._load_config_btn.setObjectName("loadConfigButton")
        self._load_config_btn.setToolTip("Récupère la config depuis config.json et tente de se connecter aux équipements.")
        layout.addWidget(self._load_config_btn)
        self._detect_btn = QPushButton("Détecter")
        self._detect_btn.setObjectName("detectButton")
        layout.addWidget(self._detect_btn)
        self._params_btn = QPushButton("Paramètres")
        self._params_btn.setObjectName("paramsButton")
        self._params_btn.setToolTip(
            "Configuration série : port, débit, timeouts (multimètre et générateur). "
            "Affiche les valeurs de config.json ; OK applique et reconnecte. Sauvegarder avec Fichier → Sauvegarder config."
        )
        layout.addWidget(self._params_btn)

        main_layout.addLayout(layout)

        self._progress = QProgressBar()
        self._progress.setMaximumHeight(6)
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        main_layout.addWidget(self._progress)

    def show_detection_progress(self) -> None:
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._detect_btn.setEnabled(False)

    def hide_detection_progress(self) -> None:
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)
        self._detect_btn.setEnabled(True)

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

    def get_load_config_button(self):
        return self._load_config_btn

    def get_params_button(self):
        return self._params_btn

    def get_detect_button(self):
        return self._detect_btn
