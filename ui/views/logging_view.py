"""
Vue onglet Enregistrement — config, démarrage/arrêt, CSV horodaté.
Connectée à core.DataLogger et core.Measurement.
"""
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QComboBox,
    QLineEdit,
    QFrame,
    QFileDialog,
    QMessageBox,
)


class LoggingView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_logger = None
        self._build_ui()

    def set_data_logger(self, data_logger):
        """Injection du DataLogger (depuis main_window)."""
        self._data_logger = data_logger
        if data_logger:
            data_logger.set_on_point_callback(self._on_log_point)

    def _on_log_point(self, timestamp_iso, elapsed_s, value, unit, mode):
        """Callback à chaque point enregistré (mise à jour affichage)."""
        self._status_label.setText(f"Dernier point : {elapsed_s:.0f} s — {value} {unit}")
        self._last_value_label.setText(f"{value} {unit}")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel(
            "Enregistrement des mesures du multimètre OWON à intervalle régulier : valeur, unité et mode "
            "dans un fichier CSV horodaté. Le générateur n'est pas enregistré."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-style: italic; padding: 4px 0;")
        layout.addWidget(info)

        config_gb = QGroupBox("Configuration enregistrement")
        config_layout = QHBoxLayout(config_gb)
        config_layout.addWidget(QLabel("Intervalle"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 86400)
        self._interval_spin.setValue(5)
        config_layout.addWidget(self._interval_spin)
        self._interval_unit = QComboBox()
        self._interval_unit.addItems(["s", "min", "h"])
        config_layout.addWidget(self._interval_unit)
        config_layout.addWidget(QLabel("Dossier"))
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText("./logs")
        self._folder_edit.setText("./logs")
        config_layout.addWidget(self._folder_edit)
        browse_btn = QPushButton("Parcourir")
        browse_btn.clicked.connect(self._on_browse)
        config_layout.addWidget(browse_btn)
        layout.addWidget(config_gb)

        self._status_label = QLabel("Arrêté")
        self._status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._status_label)
        self._last_value_label = QLabel("—")
        self._last_value_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self._last_value_label)

        graph_placeholder = QFrame()
        graph_placeholder.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        graph_placeholder.setMinimumHeight(200)
        graph_placeholder.setStyleSheet("background-color: #2d2d2d;")
        layout.addWidget(QLabel("Graphique temps réel (à venir)"))
        layout.addWidget(graph_placeholder)

        btns = QHBoxLayout()
        self._start_btn = QPushButton("Démarrer")
        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn = QPushButton("Arrêter")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        btns.addWidget(self._start_btn)
        btns.addWidget(self._stop_btn)
        btns.addWidget(QPushButton("Ouvrir fichier"))
        btns.addWidget(QPushButton("Exporter image"))
        layout.addLayout(btns)
        layout.addStretch()

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Dossier d'enregistrement")
        if path:
            self._folder_edit.setText(path)

    def _interval_seconds(self) -> float:
        v = self._interval_spin.value()
        u = self._interval_unit.currentText()
        if u == "min":
            return v * 60
        if u == "h":
            return v * 3600
        return float(v)

    def _on_start(self):
        if not self._data_logger:
            QMessageBox.warning(self, "Enregistrement", "Multimètre non connecté.")
            return
        output_dir = self._folder_edit.text().strip() or "./logs"
        interval_s = self._interval_seconds()
        path = self._data_logger.start(output_dir=output_dir, interval_s=interval_s)
        if path:
            self._status_label.setText(f"Enregistrement : {Path(path).name}")
            self._start_btn.setEnabled(False)
            self._stop_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, "Enregistrement", "Impossible de démarrer (vérifiez le dossier).")

    def _on_stop(self):
        if self._data_logger:
            self._data_logger.stop()
        self._status_label.setText("Arrêté")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def load_config(self, config: dict):
        """Charge dossier et intervalle depuis config."""
        log_cfg = config.get("logging", {})
        self._folder_edit.setText(log_cfg.get("output_dir", "./logs"))
        self._interval_spin.setValue(int(log_cfg.get("default_interval_s", 5)))
