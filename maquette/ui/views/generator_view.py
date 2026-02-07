"""
Vue onglet Générateur FY6900 — maquette, pas d'envoi de commandes.
Le FY6900 a deux voies ; les paramètres s'appliquent à la voie sélectionnée.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QRadioButton,
    QButtonGroup,
    QFormLayout,
)


class GeneratorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Sélection de la voie (FY6900 = 2 voies)
        channel_gb = QGroupBox("Voie")
        channel_layout = QHBoxLayout(channel_gb)
        self._channel_group = QButtonGroup(self)
        self._channel_1 = QRadioButton("Voie 1")
        self._channel_2 = QRadioButton("Voie 2")
        self._channel_1.setChecked(True)
        self._channel_group.addButton(self._channel_1)
        self._channel_group.addButton(self._channel_2)
        channel_layout.addWidget(self._channel_1)
        channel_layout.addWidget(self._channel_2)
        channel_layout.addWidget(QLabel("(les paramètres ci‑dessous s’appliquent à la voie choisie)"))
        channel_layout.addStretch()
        layout.addWidget(channel_gb)

        form_gb = QGroupBox("Paramètres générateur")
        form = QFormLayout(form_gb)
        form.addRow("Forme d'onde", QComboBox())  # Sinus, Triangle, Carré...
        form.addRow("Fréquence (Hz)", QDoubleSpinBox())
        form.addRow("Amplitude (V crête)", QDoubleSpinBox())
        form.addRow("Offset (V)", QDoubleSpinBox())
        layout.addWidget(form_gb)

        out_gb = QGroupBox("Sortie")
        out_layout = QHBoxLayout(out_gb)
        out_layout.addWidget(QLabel("Sortie de la voie sélectionnée :"))
        out_layout.addWidget(QRadioButton("OFF"))
        out_layout.addWidget(QRadioButton("ON"))
        layout.addWidget(out_gb)

        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Appliquer"))
        btns.addWidget(QPushButton("Sortie ON"))
        btns.addWidget(QPushButton("Sortie OFF"))
        layout.addLayout(btns)
        layout.addStretch()

    def get_selected_channel(self) -> int:
        """Retourne 1 ou 2 selon la voie sélectionnée (pour brancher le protocole FY6900)."""
        return 2 if self._channel_2.isChecked() else 1
