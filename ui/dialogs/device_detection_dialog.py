"""
Dialogue « Détecter les équipements » — à brancher sur core.device_detection.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QDialogButtonBox,
    QTextEdit,
    QProgressBar,
)


class DeviceDetectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détecter les équipements")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        desc = QLabel(
            "Parcourt les ports COM et identifie le multimètre OWON (SCPI *IDN?) "
            "et le générateur FY6900. Les ports détectés peuvent être enregistrés dans config.json."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        result_gb = QGroupBox("Résultat de la détection")
        result_layout = QVBoxLayout(result_gb)
        self._result_edit = QTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setPlaceholderText(
            "Après « Lancer la détection », les ports trouvés s'afficheront ici."
        )
        self._result_edit.setMaximumHeight(120)
        result_layout.addWidget(self._result_edit)
        layout.addWidget(result_gb)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        btn_layout = QHBoxLayout()
        self._detect_btn = QPushButton("Lancer la détection")
        self._detect_btn.clicked.connect(self._on_detect)
        btn_layout.addWidget(self._detect_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._update_config_btn = QPushButton("Mettre à jour config.json")
        self._update_config_btn.setEnabled(False)
        self._update_config_btn.clicked.connect(self._on_update_config)
        layout.addWidget(self._update_config_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_detect(self):
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._detect_btn.setEnabled(False)
        self._result_edit.clear()
        self._result_edit.append("(Détection à brancher sur core.device_detection)")
        self._progress.setVisible(False)
        self._detect_btn.setEnabled(True)
        self._update_config_btn.setEnabled(True)

    def _on_update_config(self):
        self._result_edit.append("\n→ config.json mis à jour.")
