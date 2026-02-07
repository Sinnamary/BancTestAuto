"""
Vue onglet Enregistrement — config, démarrage/arrêt, CSV horodaté.
Graphique temps réel (pyqtgraph), relecture de fichiers CSV, comparaison de courbes.
Connectée à core.DataLogger et core.Measurement.
"""
import csv
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, Qt
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
    QFileDialog,
    QMessageBox,
)

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget
    _HAS_PYQTGRAPH = True
except ImportError:
    _HAS_PYQTGRAPH = False
    PlotWidget = None


# Couleurs pour les courbes chargées (comparaison)
LOAD_COLORS = ["#e74c3c", "#2ecc71", "#3498db", "#9b59b6", "#f39c12"]


class LoggingView(QWidget):
    """Vue enregistrement avec graphique temps réel, relecture et comparaison."""

    # Signal émis depuis le callback (thread logger) pour mise à jour graphique dans le thread UI
    point_added = pyqtSignal(float, float)  # elapsed_s, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_logger = None
        self._live_t = []
        self._live_y = []
        self._loaded_curves = []  # list of (curve, t_list, y_list, label)
        self._build_ui()
        self.point_added.connect(self._on_point_added)

    def set_data_logger(self, data_logger):
        """Injection du DataLogger (depuis main_window)."""
        self._data_logger = data_logger
        if data_logger:
            data_logger.set_on_point_callback(self._on_log_point)

    def _on_log_point(self, timestamp_iso, elapsed_s, value, unit, mode):
        """Callback à chaque point enregistré (peut être appelé depuis un thread)."""
        self._status_label.setText(f"Dernier point : {elapsed_s:.0f} s — {value} {unit}")
        self._last_value_label.setText(f"{value} {unit}")
        try:
            v = float(str(value).strip().replace(",", "."))
        except (ValueError, TypeError):
            v = float("nan")
        self.point_added.emit(float(elapsed_s), v)

    def _on_point_added(self, elapsed_s: float, value: float):
        """Slot (thread principal) : ajoute un point au graphique temps réel."""
        self._live_t.append(elapsed_s)
        self._live_y.append(value)
        if self._live_curve is not None:
            self._live_curve.setData(self._live_t, self._live_y)

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

        if _HAS_PYQTGRAPH and PlotWidget is not None:
            self._plot_widget = PlotWidget()
            self._plot_widget.setBackground("k")
            self._plot_widget.setLabel("left", "Valeur")
            self._plot_widget.setLabel("bottom", "Temps écoulé (s)")
            self._plot_widget.addLegend()
            self._live_curve = self._plot_widget.plot(
                [], [], pen=pg.mkPen("y", width=2), name="Enregistrement"
            )
            self._plot_widget.setMinimumHeight(250)
            layout.addWidget(self._plot_widget)
        else:
            self._plot_widget = None
            self._live_curve = None
            layout.addWidget(QLabel("Graphique : installez pyqtgraph pour afficher les courbes."))

        btns = QHBoxLayout()
        self._start_btn = QPushButton("Démarrer")
        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn = QPushButton("Arrêter")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        btns.addWidget(self._start_btn)
        btns.addWidget(self._stop_btn)
        open_btn = QPushButton("Ouvrir fichier CSV...")
        open_btn.clicked.connect(self._on_open_file)
        btns.addWidget(open_btn)
        clear_btn = QPushButton("Effacer relecture")
        clear_btn.clicked.connect(self._on_clear_loaded)
        btns.addWidget(clear_btn)
        export_btn = QPushButton("Exporter image...")
        export_btn.clicked.connect(self._on_export_image)
        btns.addWidget(export_btn)
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
            self._live_t.clear()
            self._live_y.clear()
            if self._live_curve is not None:
                self._live_curve.setData([], [])
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

    def _parse_log_csv(self, filepath: Path):
        """Parse un CSV owon_log_*. Retourne (list_t, list_y) ou (None, None) en cas d'erreur."""
        t_list, y_list = [], []
        try:
            with open(filepath, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter=",")
                if not reader.fieldnames:
                    return None, None
                for row in reader:
                    try:
                        elapsed = float(row.get("elapsed_s", 0))
                        val_str = row.get("value", "0").strip().replace(",", ".")
                        val = float(val_str)
                    except (ValueError, KeyError):
                        continue
                    t_list.append(elapsed)
                    y_list.append(val)
        except Exception:
            return None, None
        return (t_list, y_list) if t_list else (None, None)

    def _on_open_file(self):
        """Charge un fichier CSV et affiche la courbe sur le graphique (comparaison)."""
        if not _HAS_PYQTGRAPH or self._plot_widget is None:
            QMessageBox.information(
                self, "Relecture",
                "Installez pyqtgraph pour afficher les courbes."
            )
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier CSV (enregistrement)",
            "", "CSV (*.csv);;Tous (*.*)"
        )
        if not path:
            return
        path = Path(path)
        t_list, y_list = self._parse_log_csv(path)
        if t_list is None or not t_list:
            QMessageBox.warning(
                self, "Relecture",
                "Impossible de lire le fichier ou fichier vide."
            )
            return
        color = LOAD_COLORS[len(self._loaded_curves) % len(LOAD_COLORS)]
        curve = self._plot_widget.plot(
            t_list, y_list,
            pen=pg.mkPen(color, width=1.5),
            name=path.stem[:20] + ("..." if len(path.stem) > 20 else "")
        )
        self._loaded_curves.append((curve, t_list, y_list, path.stem))
        QMessageBox.information(
            self, "Relecture",
            f"Courbe chargée : {path.name} ({len(t_list)} points)."
        )

    def _on_clear_loaded(self):
        """Supprime toutes les courbes chargées (relecture)."""
        if not _HAS_PYQTGRAPH or self._plot_widget is None:
            return
        for curve, _, _, _ in self._loaded_curves:
            self._plot_widget.removeItem(curve)
        self._loaded_curves.clear()

    def _on_export_image(self):
        """Exporte le graphique en image (PNG)."""
        if not _HAS_PYQTGRAPH or self._plot_widget is None:
            QMessageBox.information(
                self, "Export",
                "Aucun graphique à exporter (pyqtgraph requis)."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter l'image du graphique",
            "", "PNG (*.png);;Tous (*.*)"
        )
        if path:
            try:
                exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
                exporter.export(path)
                QMessageBox.information(self, "Export", f"Image enregistrée : {path}")
            except Exception as e:
                QMessageBox.warning(self, "Export", f"Erreur : {e}")

    def load_config(self, config: dict):
        """Charge dossier et intervalle depuis config."""
        log_cfg = config.get("logging", {})
        self._folder_edit.setText(log_cfg.get("output_dir", "./logs"))
        self._interval_spin.setValue(int(log_cfg.get("default_interval_s", 5)))
