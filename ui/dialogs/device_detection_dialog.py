"""
Dialogue « Détecter les équipements » — utilise core.device_detection.
Lance la détection dans un thread, affiche le résultat et le log série détaillé, permet de mettre à jour config.json.

REMOVE_AFTER_PHASE5: Dialogue actuel 2 équipements. Remplacer par un dialogue 4 équipements
utilisant core.detection.run_detection et BenchDetectionResult, puis supprimer ce fichier.
Voir docs/DEVELOPPEMENT.md.
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
try:
    from core.device_detection import detect_devices, update_config_ports, list_serial_ports
except ImportError:
    detect_devices = update_config_ports = list_serial_ports = None

from ui.workers import DetectionWorker


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
        self._multimeter_baud = None
        self._generator_port = None
        self._generator_baud = None
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

        serial_log_gb = QGroupBox("Log série détaillé (détection)")
        serial_log_layout = QVBoxLayout(serial_log_gb)
        self._serial_log_edit = QTextEdit()
        self._serial_log_edit.setReadOnly(True)
        self._serial_log_edit.setPlaceholderText(
            "Lancez la détection pour afficher ici le détail par port : émission (TX), réception (RX), débit."
        )
        self._serial_log_edit.setMinimumHeight(200)
        self._serial_log_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        serial_log_layout.addWidget(self._serial_log_edit)
        layout.addWidget(serial_log_gb)

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

    def _on_detection_result(self, multimeter_port, multimeter_baud, generator_port, generator_baud, log_lines):
        self._multimeter_port = multimeter_port
        self._multimeter_baud = multimeter_baud
        self._generator_port = generator_port
        self._generator_baud = generator_baud
        self._result_edit.clear()

        def _baud_str(b: int | None) -> str:
            if b is None:
                return ""
            return f" — débit utilisé lors du test : {b} bauds (8N1)"

        if multimeter_port:
            self._result_edit.append(f"Multimètre OWON : {multimeter_port}{_baud_str(multimeter_baud)}")
        else:
            self._result_edit.append("Multimètre OWON : non détecté")
        if generator_port:
            self._result_edit.append(f"Générateur FY6900 : {generator_port}{_baud_str(generator_baud)}")
        else:
            self._result_edit.append("Générateur FY6900 : non détecté")
        self._result_edit.append("")
        self._result_edit.append("Ces débits sont ceux pour lesquels l’appareil a répondu. Pour en utiliser un autre, modifiez config.json (ou Fichier → Ouvrir la configuration) puis rechargez la config.")
        self._update_config_btn.setEnabled(True)
        self._serial_log_edit.setPlainText("\n".join(log_lines) if log_lines else "")

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
            multimeter_baud=self._multimeter_baud,
            generator_baud=self._generator_baud,
        )
        if self._on_config_updated:
            self._on_config_updated(self._config)
        self._result_edit.append("\n→ config en mémoire mise à jour. Enregistrez avec Fichier → Sauvegarder config pour écrire config.json.")
