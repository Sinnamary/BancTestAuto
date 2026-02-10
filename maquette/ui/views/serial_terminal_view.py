"""
Vue maquette « Terminal série ».
Pas de communication réelle : zone de texte pour valider la disposition générale.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QPlainTextEdit,
    QLineEdit,
)


class SerialTerminalView(QWidget):
    """
    Maquette de l'onglet « Terminal série ».

    Montre :
    - la sélection du port,
    - la console RX/TX,
    - un champ de saisie pour les commandes.
    Aucune ouverture de port réel n'est effectuée.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        top_gb = QGroupBox("Connexion (maquette)")
        top_layout = QHBoxLayout(top_gb)
        top_layout.addWidget(QLabel("Port :"))
        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        self._port_combo.setPlaceholderText("COM1, COM2, /dev/ttyUSB0, ...")
        top_layout.addWidget(self._port_combo)
        self._connect_btn = QPushButton("Connexion")
        self._connect_btn.setEnabled(False)
        top_layout.addWidget(self._connect_btn)
        top_layout.addStretch()
        layout.addWidget(top_gb)

        self._console = QPlainTextEdit()
        self._console.setReadOnly(True)
        self._console.setPlaceholderText(
            "Affichage des échanges série (maquette).\n"
            "Aucun port n'est réellement ouvert."
        )
        layout.addWidget(self._console)

        bottom = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Saisir une commande SCPI ou texte libre (maquette)")
        bottom.addWidget(self._input)
        self._send_btn = QPushButton("Envoyer")
        self._send_btn.setEnabled(False)
        bottom.addWidget(self._send_btn)
        layout.addLayout(bottom)

        layout.addStretch()

