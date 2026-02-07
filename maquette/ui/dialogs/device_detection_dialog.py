"""
Dialogue squelette « Détecter les équipements ».
Parcourt les ports COM, identifie multimètre OWON (SCPI *IDN?) et générateur FY6900,
affiche le résultat et permet de mettre à jour config.json.
En maquette : pas de vraie détection, uniquement l’interface.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QProgressBar,
    QDialogButtonBox,
    QTextEdit,
)


class DeviceDetectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détecter les équipements")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Explication
        desc = QLabel(
            "Parcourt les ports COM disponibles et identifie le multimètre OWON (SCPI *IDN?) "
            "et le générateur FY6900 par protocole. Les ports détectés peuvent être enregistrés dans config.json."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Zone résultat (squelette)
        result_gb = QGroupBox("Résultat de la détection")
        result_layout = QVBoxLayout(result_gb)
        self._result_edit = QTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setPlaceholderText(
            "Après « Lancer la détection », les ports trouvés s’afficheront ici.\n"
            "Ex. Multimètre OWON : COM3 — Générateur FY6900 : COM4"
        )
        self._result_edit.setMaximumHeight(120)
        result_layout.addWidget(self._result_edit)
        layout.addWidget(result_gb)

        # Barre de progression (visible pendant la détection)
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Boutons d’action
        btn_layout = QHBoxLayout()
        self._detect_btn = QPushButton("Lancer la détection")
        self._detect_btn.clicked.connect(self._on_detect)
        btn_layout.addWidget(self._detect_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Mise à jour config
        self._update_config_btn = QPushButton("Mettre à jour config.json")
        self._update_config_btn.setEnabled(False)  # activé après une détection réussie
        self._update_config_btn.clicked.connect(self._on_update_config)
        layout.addWidget(self._update_config_btn)

        # Fermer
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_detect(self):
        # Squelette : pas de vraie détection, simulation pour la maquette
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)  # mode indéterminé
        self._detect_btn.setEnabled(False)
        self._result_edit.clear()
        self._result_edit.append("(Maquette : simulation de détection…)")
        # En intégration : appel à core.device_detection + mise à jour du texte
        self._result_edit.append("Multimètre OWON : COM3")
        self._result_edit.append("Générateur FY6900 : COM4")
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)
        self._detect_btn.setEnabled(True)
        self._update_config_btn.setEnabled(True)

    def _on_update_config(self):
        # Squelette : à brancher sur device_detection + settings
        self._result_edit.append("\n→ config.json mis à jour (maquette : non enregistré).")
