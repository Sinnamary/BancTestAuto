"""
Vue onglet Banc de test filtre : config balayage, tableau, graphique Bode, export.
Connectée au core (FilterTest) ; balayage en QThread.
"""
import csv
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QFrame,
    QRadioButton,
    QButtonGroup,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

try:
    from ui.views.bode_plot_widget import BodePlotWidget
    _BODE_PLOT_AVAILABLE = True
except ImportError:
    _BODE_PLOT_AVAILABLE = False
    BodePlotWidget = None


# Worker thread pour exécuter le balayage sans bloquer l'UI
class SweepWorker(QThread):
    point_received = pyqtSignal(object, int, int)  # BodePoint, index, total
    progress = pyqtSignal(int, int)
    finished_sweep = pyqtSignal(list)  # list[BodePoint]
    error = pyqtSignal(str)

    def __init__(self, filter_test):
        super().__init__()
        self._filter_test = filter_test

    def run(self):
        try:
            results = self._filter_test.run_sweep(
                on_point=lambda p, i, t: self.point_received.emit(p, i, t),
                on_progress=lambda i, t: self.progress.emit(i, t),
            )
            self.finished_sweep.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class FilterTestView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_test = None
        self._worker = None
        self._results: list = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        config_gb = QGroupBox("Balayage en fréquence")
        config_layout = QVBoxLayout(config_gb)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Voie générateur FY6900 :"))
        self._channel_group = QButtonGroup(self)
        self._channel_1 = QRadioButton("Voie 1")
        self._channel_2 = QRadioButton("Voie 2")
        self._channel_1.setChecked(True)
        self._channel_group.addButton(self._channel_1)
        self._channel_group.addButton(self._channel_2)
        row1.addWidget(self._channel_1)
        row1.addWidget(self._channel_2)
        row1.addSpacing(24)
        row1.addWidget(QLabel("f_min (Hz)"))
        self._f_min = QDoubleSpinBox()
        self._f_min.setRange(0.1, 100e6)
        self._f_min.setValue(10)
        self._f_min.setDecimals(2)
        row1.addWidget(self._f_min)
        row1.addWidget(QLabel("f_max (Hz)"))
        self._f_max = QDoubleSpinBox()
        self._f_max.setRange(1, 100e6)
        self._f_max.setValue(100000)
        self._f_max.setDecimals(0)
        row1.addWidget(self._f_max)
        row1.addWidget(QLabel("Points"))
        self._n_points = QSpinBox()
        self._n_points.setRange(2, 500)
        self._n_points.setValue(50)
        row1.addWidget(self._n_points)
        row1.addWidget(QLabel("Échelle"))
        self._scale_combo = QComboBox()
        self._scale_combo.addItems(["log", "lin"])
        row1.addWidget(self._scale_combo)
        row1.addStretch()
        config_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Délai (ms)"))
        self._settling_ms = QSpinBox()
        self._settling_ms.setRange(50, 2000)
        self._settling_ms.setValue(200)
        row2.addWidget(self._settling_ms)
        row2.addWidget(QLabel("Ue (V RMS)"))
        self._ue_rms = QDoubleSpinBox()
        self._ue_rms.setRange(0.01, 100)
        self._ue_rms.setValue(1.0)
        self._ue_rms.setDecimals(2)
        row2.addWidget(self._ue_rms)
        row2.addStretch()
        config_layout.addLayout(row2)

        layout.addWidget(config_gb)

        btns = QHBoxLayout()
        self._start_btn = QPushButton("Démarrer balayage")
        self._stop_btn = QPushButton("Arrêter")
        self._stop_btn.setEnabled(False)
        self._export_csv_btn = QPushButton("Exporter CSV")
        self._export_graph_btn = QPushButton("Exporter graphique")
        btns.addWidget(self._start_btn)
        btns.addWidget(self._stop_btn)
        btns.addWidget(self._export_csv_btn)
        btns.addWidget(self._export_graph_btn)
        layout.addLayout(btns)

        self._progress = QProgressBar()
        self._progress.setMaximum(100)
        layout.addWidget(self._progress)

        table_gb = QGroupBox("Résultats")
        table_layout = QVBoxLayout(table_gb)
        self._results_table = QTableWidget(0, 4)
        self._results_table.setHorizontalHeaderLabels(["f (Hz)", "Us (V)", "Us/Ue", "Gain (dB)"])
        table_layout.addWidget(self._results_table)
        layout.addWidget(table_gb)

        graph_desc = QLabel(
            "Graphique Bode — Axe X : fréquence (Hz), échelle logarithmique. "
            "Axe Y : gain en dB (20×log₁₀(Us/Ue))."
        )
        graph_desc.setWordWrap(True)
        graph_desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(graph_desc)

        y_axis_gb = QGroupBox("Ordonnée (Y)")
        y_axis_layout = QHBoxLayout(y_axis_gb)
        self._y_axis_group = QButtonGroup(self)
        self._y_linear = QRadioButton("Gain linéaire (Us/Ue)")
        self._y_db = QRadioButton("Gain en dB")
        self._y_db.setChecked(True)
        self._y_axis_group.addButton(self._y_linear)
        self._y_axis_group.addButton(self._y_db)
        y_axis_layout.addWidget(self._y_linear)
        y_axis_layout.addWidget(self._y_db)
        layout.addWidget(y_axis_gb)

        if _BODE_PLOT_AVAILABLE and BodePlotWidget:
            self._bode_plot = BodePlotWidget()
            self._bode_plot.setMinimumHeight(200)
            layout.addWidget(self._bode_plot)
        else:
            self._bode_plot = None
            graph_placeholder = QFrame()
            graph_placeholder.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
            graph_placeholder.setMinimumHeight(200)
            graph_placeholder.setStyleSheet("background-color: #2d2d2d;")
            layout.addWidget(graph_placeholder)
        layout.addStretch()

        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn.clicked.connect(self._on_stop)
        self._export_csv_btn.clicked.connect(self._on_export_csv)
        self._export_graph_btn.clicked.connect(self._on_export_graph)

    def set_filter_test(self, filter_test):
        """Injection du banc filtre (FilterTest) depuis la fenêtre principale."""
        self._filter_test = filter_test

    def load_config(self, config: dict):
        """Charge les valeurs depuis la section filter_test de la config."""
        ft = config.get("filter_test", {})
        self._f_min.setValue(float(ft.get("f_min_hz", 10)))
        self._f_max.setValue(float(ft.get("f_max_hz", 100000)))
        self._n_points.setValue(int(ft.get("n_points", 50)))
        self._settling_ms.setValue(int(ft.get("settling_ms", 200)))
        self._ue_rms.setValue(float(ft.get("ue_rms", 1.0)))
        scale = ft.get("scale", "log")
        idx = self._scale_combo.findText(scale)
        if idx >= 0:
            self._scale_combo.setCurrentIndex(idx)
        ch = int(ft.get("generator_channel", 1))
        self._channel_1.setChecked(ch == 1)
        self._channel_2.setChecked(ch == 2)

    def get_filter_test_config(self):
        """Retourne un dict compatible avec FilterTestConfig (pour le core)."""
        return {
            "generator_channel": 2 if self._channel_2.isChecked() else 1,
            "f_min_hz": self._f_min.value(),
            "f_max_hz": self._f_max.value(),
            "n_points": self._n_points.value(),
            "scale": self._scale_combo.currentText(),
            "settling_ms": self._settling_ms.value(),
            "ue_rms": self._ue_rms.value(),
        }

    def _on_start(self):
        if not self._filter_test:
            QMessageBox.warning(self, "Banc filtre", "Connexion multimètre/générateur requise.")
            return
        from core.filter_test import FilterTestConfig
        cfg = FilterTestConfig(**self.get_filter_test_config())
        self._filter_test.set_config(cfg)
        self._results_table.setRowCount(0)
        self._results = []
        if self._bode_plot:
            self._bode_plot.clear()
        self._progress.setValue(0)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._worker = SweepWorker(self._filter_test)
        self._worker.point_received.connect(self._on_point)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_sweep.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self):
        if self._filter_test:
            self._filter_test.abort()

    def _on_point(self, point, index, total):
        self._results.append(point)
        row = self._results_table.rowCount()
        self._results_table.insertRow(row)
        self._results_table.setItem(row, 0, QTableWidgetItem(f"{point.f_hz:.4g}"))
        self._results_table.setItem(row, 1, QTableWidgetItem(f"{point.us_v:.6f}"))
        self._results_table.setItem(row, 2, QTableWidgetItem(f"{point.gain_linear:.6f}"))
        self._results_table.setItem(row, 3, QTableWidgetItem(f"{point.gain_db:.2f}"))
        if self._bode_plot:
            self._bode_plot.set_bode_points(self._results)

    def _on_progress(self, current, total):
        self._progress.setMaximum(total)
        self._progress.setValue(current)

    def _on_finished(self, results):
        self._results = results
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.setValue(self._progress.maximum())

    def _on_error(self, msg):
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        QMessageBox.critical(self, "Erreur balayage", msg)

    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter CSV", "", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["f_Hz", "Us_V", "Us_Ue", "Gain_dB"])
            for p in self._results:
                w.writerow([p.f_hz, p.us_v, p.gain_linear, p.gain_db])
        QMessageBox.information(self, "Export", f"CSV enregistré : {path}")

    def _on_export_graph(self):
        if not self._bode_plot:
            QMessageBox.information(
                self, "Export graphique",
                "Installez pyqtgraph pour activer l'export du graphique Bode.",
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter graphique Bode", "", "PNG (*.png);;Tous (*)"
        )
        if not path:
            return
        if self._bode_plot.export_image(path):
            QMessageBox.information(self, "Export", f"Graphique enregistré : {path}")
        else:
            QMessageBox.warning(self, "Export", "Échec de l'export de l'image.")

    def get_generator_channel(self) -> int:
        return 2 if self._channel_2.isChecked() else 1

    def is_gain_in_db(self) -> bool:
        return self._y_db.isChecked()
