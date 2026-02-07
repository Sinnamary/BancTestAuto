"""
Dialogue « Détecter les équipements » — utilise core.device_detection.
Lance la détection dans un thread, affiche le résultat, permet de mettre à jour config.json.
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
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from core.device_detection import detect_devices, update_config_ports, list_serial_ports
except ImportError:
    detect_devices = update_config_ports = list_serial_ports = None


class DetectionWorker(QThread):
    """Thread pour exécuter la détection sans bloquer l'UI."""
    result = pyqtSignal(object, object)  # multimeter_port, generator_port

    def run(self):
        if detect_devices is None:
            self.result.emit(None, None)
            return
        multimeter_port, generator_port = detect_devices()
        self.result.emit(multimeter_port, generator_port)


class DeviceDetectionDialog(QDialog):
    def __init__(self, parent=None, config: dict = None, on_config_updated=None):
        """
        config: dict config courant (pour mise à jour des ports).
        on_config_updated: callback(config_dict) appelé après « Mettre à jour config ».
        """
        super().__init__(parent)
        self.setWindowTitle("Détecter les équipements")
        self.setMinimumWidth(420)
        self._config = config or {}
        self._on_config_updated = on_config_updated
        self._multimeter_port = None
        self._generator_port = None
        self._worker = None
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
        if detect_devices is None:
            self._result_edit.clear()
            self._result_edit.append("Module core.device_detection non disponible.")
            return
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._detect_btn.setEnabled(False)
        self._result_edit.clear()
        self._result_edit.append("Scan des ports en cours…")
        self._worker = DetectionWorker()
        self._worker.result.connect(self._on_detection_result)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_detection_result(self, multimeter_port, generator_port):
        self._multimeter_port = multimeter_port
        self._generator_port = generator_port
        self._result_edit.clear()
        if multimeter_port:
            self._result_edit.append(f"Multimètre OWON : {multimeter_port}")
        else:
            self._result_edit.append("Multimètre OWON : non détecté")
        if generator_port:
            self._result_edit.append(f"Générateur FY6900 : {generator_port}")
        else:
            self._result_edit.append("Générateur FY6900 : non détecté")
        self._update_config_btn.setEnabled(True)

    def _on_worker_finished(self):
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)
        self._detect_btn.setEnabled(True)

    def _on_update_config(self):
        if update_config_ports is None:
            self._result_edit.append("\n→ Mise à jour config non disponible.")
            return
        self._config = update_config_ports(
            self._config,
            self._multimeter_port,
            self._generator_port,
        )
        if self._on_config_updated:
            self._on_config_updated(self._config)
        self._result_edit.append("\n→ config en mémoire mise à jour. Enregistrez avec Fichier → Sauvegarder config pour écrire config.json.")
