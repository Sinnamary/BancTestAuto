"""
Dialogue « Détecter les équipements » (4 équipements) — Phase 2.
Utilise core.detection.run_detection(bench_equipment_kinds(), log_lines) et BenchDetectionResult.
Affiche Multimètre, Générateur, Alimentation, Oscilloscope ; met à jour config via update_config_from_detection.
"""
from pathlib import Path

import sys

# Rendre core.detection importable depuis la maquette (maquette n'a pas core/detection/)
_path = Path(__file__).resolve().parent
for _ in range(10):
    if (_path / "core" / "detection" / "__init__.py").exists():
        if str(_path) not in sys.path:
            sys.path.insert(0, str(_path))
        break
    _path = _path.parent
else:
    _path = None

try:
    from core.detection import run_detection, update_config_from_detection, list_serial_ports
    from core.equipment import bench_equipment_kinds, EquipmentKind, equipment_display_name
    from core.detection.result import BenchDetectionResult, SerialDetectionResult, UsbDetectionResult
except ImportError:
    run_detection = update_config_from_detection = list_serial_ports = None
    bench_equipment_kinds = None
    EquipmentKind = None
    equipment_display_name = lambda k: str(k)
    BenchDetectionResult = SerialDetectionResult = UsbDetectionResult = None

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
    QFormLayout,
)


class DeviceDetectionDialog4(QDialog):
    """Dialogue de détection pour les 4 équipements (Multimètre, Générateur, Alimentation, Oscilloscope)."""

    def __init__(self, parent=None, config: dict = None, on_config_updated=None):
        super().__init__(parent)
        self.setWindowTitle("Détecter les équipements (4)")
        self.setMinimumWidth(480)
        self._config = config or {}
        self._on_config_updated = on_config_updated
        self._last_result = None
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        desc = QLabel(
            "Parcourt les ports COM (et USB pour l'oscilloscope) et identifie le multimètre OWON, "
            "le générateur FY6900, l'alimentation RS305P. L'oscilloscope USB peut être configuré manuellement. "
            "Les ports détectés peuvent être enregistrés dans config.json."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        result_gb = QGroupBox("Résultat par équipement")
        result_layout = QFormLayout(result_gb)
        self._result_labels = {}
        if EquipmentKind is not None and bench_equipment_kinds is not None:
            for kind in bench_equipment_kinds():
                lbl = QLabel("—")
                lbl.setStyleSheet("font-family: Consolas, monospace;")
                self._result_labels[kind] = lbl
                result_layout.addRow(equipment_display_name(kind) + " :", lbl)
        else:
            result_layout.addRow(QLabel("Module core.detection non disponible."))
        layout.addWidget(result_gb)

        log_gb = QGroupBox("Log série détaillé (détection)")
        log_layout = QVBoxLayout(log_gb)
        self._serial_log_edit = QTextEdit()
        self._serial_log_edit.setReadOnly(True)
        self._serial_log_edit.setPlaceholderText("Lancez la détection pour afficher le détail par port.")
        self._serial_log_edit.setMinimumHeight(180)
        self._serial_log_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        log_layout.addWidget(self._serial_log_edit)
        layout.addWidget(log_gb)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        btn_layout = QHBoxLayout()
        self._detect_btn = QPushButton("Lancer la détection")
        self._detect_btn.clicked.connect(self._on_detect)
        btn_layout.addWidget(self._detect_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._update_config_btn = QPushButton("Mettre à jour config (en mémoire)")
        self._update_config_btn.setEnabled(False)
        self._update_config_btn.clicked.connect(self._on_update_config)
        layout.addWidget(self._update_config_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _format_result(self, kind, item):
        if item is None:
            return "—"
        if isinstance(item, SerialDetectionResult):
            if item.port:
                b = f" @ {item.baudrate} bauds" if item.baudrate else ""
                return f"{item.port}{b}"
            return "non détecté"
        if isinstance(item, UsbDetectionResult):
            if item.vendor_id is not None and item.product_id is not None:
                return f"VID=0x{item.vendor_id:04X} PID=0x{item.product_id:04X}"
            return "non détecté (config manuelle)"
        return "—"

    def _on_detect(self):
        if run_detection is None or bench_equipment_kinds is None:
            for lbl in self._result_labels.values():
                lbl.setText("Module core.detection non disponible.")
            return
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._detect_btn.setEnabled(False)
        for lbl in self._result_labels.values():
            lbl.setText("…")
        self._serial_log_edit.clear()
        self._serial_log_edit.setPlainText("Scan en cours…")
        from ui.workers.detection_worker_4 import DetectionWorker4

        self._worker = DetectionWorker4()
        self._worker.result.connect(self._on_detection_result)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_detection_result(self, bench_result):
        if bench_result is None:
            for lbl in getattr(self, "_result_labels", {}).values():
                lbl.setText("Module core.detection non disponible.")
            self._serial_log_edit.setPlainText("")
            return
        self._last_result = bench_result
        if EquipmentKind is not None and bench_equipment_kinds is not None and bench_result.results is not None:
            for kind in bench_equipment_kinds():
                item = bench_result.results.get(kind)
                self._result_labels[kind].setText(self._format_result(kind, item))
        self._serial_log_edit.setPlainText("\n".join(bench_result.log_lines) if bench_result.log_lines else "")
        self._update_config_btn.setEnabled(True)

    def _on_worker_finished(self):
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)
        self._detect_btn.setEnabled(True)

    def _on_update_config(self):
        if update_config_from_detection is None or self._last_result is None:
            return
        self._config = update_config_from_detection(self._config, self._last_result)
        if self._on_config_updated:
            self._on_config_updated(self._config)
        self._update_config_btn.setText("Config mise à jour — Sauvegarder avec Fichier → Sauvegarder config")
