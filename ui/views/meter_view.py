"""
Vue onglet Multimètre — affichage, modes, plage, historique.
Connectée à core.Measurement pour mesure unique et historique.
"""
import csv
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class MeasureWorker(QThread):
    """Thread pour une mesure (évite de bloquer l'UI)."""
    result = pyqtSignal(str, float, str)  # raw, value_or_nan, unit_placeholder
    error = pyqtSignal(str)

    def __init__(self, measurement):
        super().__init__()
        self._measurement = measurement

    def run(self):
        try:
            raw = self._measurement.read_value()
            val = self._measurement.parse_float(raw)
            if val is None:
                val = float("nan")
            unit = "V"  # TODO: selon le mode
            self.result.emit(raw, val, unit)
        except Exception as e:
            self.error.emit(str(e))


class MeterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._measurement = None
        self._history = []  # list of (value_str, unit)
        self._history_max = 100
        self._build_ui()

    def set_measurement(self, measurement):
        """Injection de la couche mesure (depuis main_window)."""
        self._measurement = measurement

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        layout = QVBoxLayout(content)

        modes_gb = QGroupBox("Modes de mesure")
        modes_layout = QHBoxLayout(modes_gb)
        modes_layout.setSpacing(4)
        self._mode_group = QButtonGroup(self)
        modes = ["V⎓", "V~", "A⎓", "A~", "Ω", "Ω 4W", "Hz", "s", "F", "°C", "⊿", "⚡"]
        _mode_btn_style = (
            "QPushButton { font-size: 11px; padding: 2px 6px; min-width: 32px; max-height: 22px; }"
        )
        for m in modes:
            btn = QPushButton(m)
            btn.setCheckable(True)
            btn.setStyleSheet(_mode_btn_style)
            btn.setFixedHeight(22)
            self._mode_group.addButton(btn)
            modes_layout.addWidget(btn)
        self._mode_group.buttons()[0].setChecked(True)
        layout.addWidget(modes_gb)

        display_gb = QGroupBox("Affichage")
        display_layout = QHBoxLayout(display_gb)
        self._value_label = QLabel("—")
        self._value_label.setStyleSheet("font-size: 28px; font-family: Consolas, monospace;")
        self._value_label.setMinimumWidth(200)
        display_layout.addWidget(self._value_label)
        display_layout.addStretch()
        self._secondary_check = QCheckBox("Afficher Hz")
        display_layout.addWidget(self._secondary_check)
        self._secondary_label = QLabel("—")
        self._secondary_label.setStyleSheet("font-size: 14px;")
        display_layout.addWidget(self._secondary_label)
        layout.addWidget(display_gb)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        range_gb = QGroupBox("Plage")
        range_layout = QVBoxLayout(range_gb)
        range_layout.addWidget(QRadioButton("Auto"))
        range_layout.addWidget(QRadioButton("Manuel"))
        range_layout.addWidget(QComboBox())
        row_layout.addWidget(range_gb)
        rate_gb = QGroupBox("Vitesse")
        rate_layout = QVBoxLayout(rate_gb)
        rate_layout.addWidget(QRadioButton("Rapide"))
        rate_layout.addWidget(QRadioButton("Moyenne"))
        rate_layout.addWidget(QRadioButton("Lente"))
        row_layout.addWidget(rate_gb)
        math_gb = QGroupBox("Fonctions math")
        math_layout = QVBoxLayout(math_gb)
        math_layout.addWidget(QRadioButton("Aucun"))
        math_layout.addWidget(QRadioButton("Rel"))
        math_layout.addWidget(QRadioButton("dB"))
        math_layout.addWidget(QRadioButton("dBm"))
        math_layout.addWidget(QRadioButton("Moyenne"))
        row_layout.addWidget(math_gb)
        layout.addWidget(row)

        hist_gb = QGroupBox("Historique")
        hist_layout = QVBoxLayout(hist_gb)
        self._history_table = QTableWidget(0, 3)
        self._history_table.setHorizontalHeaderLabels(["#", "Valeur", "Unité"])
        hist_layout.addWidget(self._history_table)
        btn_row = QHBoxLayout()
        self._export_hist_btn = QPushButton("Exporter CSV")
        self._clear_hist_btn = QPushButton("Effacer")
        btn_row.addWidget(self._export_hist_btn)
        btn_row.addWidget(self._clear_hist_btn)
        hist_layout.addLayout(btn_row)
        layout.addWidget(hist_gb)

        actions = QHBoxLayout()
        self._measure_btn = QPushButton("Mesure")
        self._measure_btn.clicked.connect(self._on_measure)
        actions.addWidget(self._measure_btn)
        actions.addWidget(QPushButton("Mesure continue"))
        actions.addWidget(QPushButton("Reset (*RST)"))
        self._export_csv_btn = QPushButton("Exporter CSV")
        self._export_csv_btn.clicked.connect(self._on_export_csv)
        actions.addWidget(self._export_csv_btn)
        layout.addLayout(actions)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self._export_hist_btn.clicked.connect(self._on_export_csv)
        self._clear_hist_btn.clicked.connect(self._on_clear_history)

    def _on_measure(self):
        if not self._measurement:
            self._value_label.setText("—")
            return
        self._measure_btn.setEnabled(False)
        self._worker = MeasureWorker(self._measurement)
        self._worker.result.connect(self._on_measure_result)
        self._worker.error.connect(self._on_measure_error)
        self._worker.finished.connect(lambda: self._measure_btn.setEnabled(True))
        self._worker.start()

    def _on_measure_result(self, raw: str, value: float, unit: str):
        if value != value:  # nan
            text = raw.strip() or "—"
        else:
            text = f"{value:.4g} {unit}"
        self._value_label.setText(text)
        self._history.append((text.split()[0] if value == value else raw, unit))
        if len(self._history) > self._history_max:
            self._history.pop(0)
        self._refresh_history_table()

    def _on_measure_error(self, msg: str):
        self._value_label.setText("Err")
        QMessageBox.warning(self, "Mesure", f"Erreur : {msg}")

    def _refresh_history_table(self):
        self._history_table.setRowCount(len(self._history))
        for i, (val, unit) in enumerate(self._history):
            self._history_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._history_table.setItem(i, 1, QTableWidgetItem(val))
            self._history_table.setItem(i, 2, QTableWidgetItem(unit))

    def _on_clear_history(self):
        self._history.clear()
        self._history_table.setRowCount(0)

    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter historique CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["#", "Valeur", "Unité"])
                for i, (val, unit) in enumerate(self._history):
                    w.writerow([i + 1, val, unit])
            QMessageBox.information(self, "Export", f"Fichier enregistré : {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export", str(e))
