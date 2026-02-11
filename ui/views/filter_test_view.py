"""
Vue onglet Banc de test filtre : config balayage, tableau, graphique Bode, export.
Connectée au core (FilterTest) ; balayage en QThread.
"""
import csv
from datetime import datetime
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
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QRadioButton,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from ui.bode_csv_viewer import BodeCsvViewerDialog
from ui.bode_csv_viewer.model import BodeCsvDataset, BodeCsvPoint
from ui.workers import SweepWorker


class FilterTestView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_test = None
        self._worker = None
        self._results: list = []
        self._config: dict | None = None
        self._stabilization_dialog: QDialog | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        config_gb = QGroupBox("Balayage en fréquence")
        config_layout = QVBoxLayout(config_gb)

        row0 = QHBoxLayout()
        row0.addWidget(QLabel("Source de mesure :"))
        self._source_combo = QComboBox()
        self._source_combo.addItem("Multimètre (< 2 kHz)", "multimeter")
        self._source_combo.setItemData(0, "Seule la sortie du filtre (Us) est mesurée. Ue = valeur réglée sur le générateur (non mesurée). Limité en fréquence.", Qt.ItemDataRole.ToolTipRole)
        self._source_combo.addItem("Oscilloscope (Ch1=Ue, Ch2=Us)", "oscilloscope")
        self._source_combo.setItemData(1, "Canal 1 = Ue (génération), canal 2 = Us (sortie filtre). Mesure de la phase. Bande passante adaptée.", Qt.ItemDataRole.ToolTipRole)
        row0.addWidget(self._source_combo)
        self._source_hint_label = QLabel()
        self._update_source_hint_label()
        row0.addWidget(self._source_hint_label)
        row0.addStretch()
        config_layout.addLayout(row0)
        self._source_combo.currentIndexChanged.connect(self._update_source_hint_label)

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
        row1.addWidget(QLabel("Points par décade"))
        self._points_per_decade = QSpinBox()
        self._points_per_decade.setRange(1, 100)
        self._points_per_decade.setValue(10)
        self._points_per_decade.setToolTip(
            "Nombre de points par décade (chaque gamme ×10 : 10–100 Hz, 100–1000 Hz, etc.). Le nombre total de points est calculé automatiquement."
        )
        row1.addWidget(self._points_per_decade)
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
        self._view_graph_btn = QPushButton("Voir le graphique Bode")
        self._view_graph_btn.setEnabled(False)
        self._view_graph_btn.setToolTip("Ouvrir une fenêtre avec le graphique de réponse en fréquence (choix gain linéaire / dB)")
        btns.addWidget(self._start_btn)
        btns.addWidget(self._stop_btn)
        btns.addWidget(self._export_csv_btn)
        btns.addWidget(self._view_graph_btn)
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
        layout.addStretch()

        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn.clicked.connect(self._on_stop)
        self._export_csv_btn.clicked.connect(self._on_export_csv)
        self._view_graph_btn.clicked.connect(self._on_view_graph)

    def _update_source_hint_label(self):
        """Met à jour le libellé explicatif selon la source de mesure choisie."""
        if not hasattr(self, "_source_hint_label"):
            return
        source = self._source_combo.currentData() if hasattr(self, "_source_combo") else "multimeter"
        if source == "oscilloscope":
            self._source_hint_label.setText("  → Ch1 = Ue (génération), Ch2 = Us (sortie filtre)")
        else:
            self._source_hint_label.setText("  → Ue = valeur générateur (non mesurée), Us = mesure multimètre")

    def set_filter_test(self, filter_test):
        """Injection du banc filtre (FilterTest) depuis la fenêtre principale."""
        self._filter_test = filter_test

    def load_config(self, config: dict):
        """Charge les valeurs depuis la section filter_test de la config."""
        self._config = config
        ft = config.get("filter_test", {})
        self._f_min.setValue(float(ft.get("f_min_hz", 10)))
        self._f_max.setValue(float(ft.get("f_max_hz", 100000)))
        self._points_per_decade.setValue(int(ft.get("points_per_decade", 10)))
        self._settling_ms.setValue(int(ft.get("settling_ms", 200)))
        self._ue_rms.setValue(float(ft.get("ue_rms", 1.0)))
        ch = int(ft.get("generator_channel", 1))
        self._channel_1.setChecked(ch == 1)
        self._channel_2.setChecked(ch == 2)
        src = ft.get("measure_source", "multimeter")
        idx = self._source_combo.findData(src)
        if idx >= 0:
            self._source_combo.setCurrentIndex(idx)

    def get_filter_test_config(self):
        """Retourne un dict compatible avec FilterTestConfig (pour le core) + measure_source pour persistance."""
        return {
            "generator_channel": 2 if self._channel_2.isChecked() else 1,
            "f_min_hz": self._f_min.value(),
            "f_max_hz": self._f_max.value(),
            "points_per_decade": self._points_per_decade.value(),
            "scale": "log",
            "settling_ms": self._settling_ms.value(),
            "ue_rms": self._ue_rms.value(),
            "measure_source": self._source_combo.currentData() or "multimeter",
        }

    def _on_start(self):
        if not self._filter_test:
            source_kind = self._source_combo.currentData() or "multimeter"
            if source_kind == "oscilloscope":
                msg = "Connexion générateur et oscilloscope requise."
            else:
                msg = "Connexion multimètre et générateur requise."
            QMessageBox.warning(self, "Banc filtre", msg)
            return
        source_kind = self._source_combo.currentData() or "multimeter"
        if hasattr(self._filter_test, "set_measure_source_kind"):
            ok = self._filter_test.set_measure_source_kind(source_kind)
            if not ok and source_kind == "oscilloscope":
                QMessageBox.warning(
                    self,
                    "Banc filtre",
                    "Oscilloscope sélectionné mais non connecté ou indisponible. Connectez l'oscilloscope (Connecter tout) ou choisissez Multimètre.",
                )
                return
        from core.filter_test import FilterTestConfig
        cfg_dict = self.get_filter_test_config()
        cfg = FilterTestConfig(
            generator_channel=cfg_dict["generator_channel"],
            f_min_hz=cfg_dict["f_min_hz"],
            f_max_hz=cfg_dict["f_max_hz"],
            points_per_decade=cfg_dict["points_per_decade"],
            scale=cfg_dict["scale"],
            settling_ms=cfg_dict["settling_ms"],
            ue_rms=cfg_dict["ue_rms"],
        )
        self._filter_test.set_config(cfg)
        self._results_table.setRowCount(0)
        self._results = []
        self._view_graph_btn.setEnabled(False)
        self._progress.setValue(0)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._worker = SweepWorker(self._filter_test)
        self._worker.point_received.connect(self._on_point)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_sweep.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.stabilization_started.connect(self._on_stabilization_started)
        self._worker.stabilization_ended.connect(self._on_stabilization_ended)
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

    def _on_progress(self, current, total):
        self._progress.setMaximum(total)
        self._progress.setValue(current)

    def _on_stabilization_started(self):
        """Affiche une fenêtre « Attente stabilisation » pendant les 2 secondes."""
        self._stabilization_dialog = QDialog(self)
        self._stabilization_dialog.setWindowTitle("Banc filtre")
        self._stabilization_dialog.setModal(False)
        layout = QVBoxLayout(self._stabilization_dialog)
        layout.addWidget(QLabel("Attente stabilisation (2 s)..."))
        self._stabilization_dialog.setMinimumWidth(280)
        self._stabilization_dialog.show()

    def _on_stabilization_ended(self):
        """Ferme la fenêtre d'attente stabilisation."""
        if self._stabilization_dialog:
            self._stabilization_dialog.close()
            self._stabilization_dialog = None

    def _on_finished(self, results):
        self._results = results
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress.setValue(self._progress.maximum())
        if self._results:
            self._view_graph_btn.setEnabled(True)

    def _on_error(self, msg):
        self._on_stabilization_ended()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        QMessageBox.critical(self, "Erreur balayage", msg)

    def _on_export_csv(self):
        default_name = f"bancfiltre_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Exporter CSV", default_name, "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["f_Hz", "Us_V", "Us_Ue", "Gain_dB"])
            for p in self._results:
                w.writerow([p.f_hz, p.us_v, p.gain_linear, p.gain_db])
        QMessageBox.information(self, "Export", f"CSV enregistré : {path}")

    def _on_view_graph(self):
        """Ouvre le visualiseur Bode complet avec les données du balayage (aucun choix de fichier)."""
        if not self._results:
            QMessageBox.information(
                self, "Graphique Bode",
                "Aucun résultat de balayage. Lancez un balayage puis cliquez sur « Voir le graphique Bode ».",
            )
            return
        # Données déjà collectées : on les injecte directement dans le graphique (pas de dialogue d'ouverture de fichier)
        csv_points = [
            BodeCsvPoint(f_hz=p.f_hz, us_v=p.us_v, gain_linear=p.gain_linear, gain_db=p.gain_db)
            for p in self._results
        ]
        dataset = BodeCsvDataset(csv_points)
        config = self._config if self._config is not None else {}
        dlg = BodeCsvViewerDialog(self, csv_path="", dataset=dataset, config=config)
        dlg.setWindowTitle("Graphique Bode — Résultat balayage")
        dlg.exec()

    def get_generator_channel(self) -> int:
        return 2 if self._channel_2.isChecked() else 1

