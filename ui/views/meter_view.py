"""
Vue onglet Multimètre — affichage, modes, plage, historique.
Connectée à core.Measurement pour mesure unique et historique.
"""
import csv
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from core.measurement import MODE_IDS
from ui.widgets.measurement_display import MeasurementDisplay
from ui.widgets.history_table import HistoryTable
from ui.widgets.mode_bar import ModeBar
from ui.widgets.range_selector import RangeSelector
from ui.widgets.rate_selector import RateSelector
from ui.widgets.math_panel import MathPanel
from ui.widgets.advanced_params import AdvancedParamsPanel


# Méthodes Measurement par mode (ordre = MODE_IDS)
def _mode_setter_name(mode_id):
    _map = {
        "volt_dc": "set_voltage_dc", "volt_ac": "set_voltage_ac",
        "curr_dc": "set_current_dc", "curr_ac": "set_current_ac",
        "res": "set_resistance", "fres": "set_resistance_4w",
        "freq": "set_frequency", "per": "set_period", "cap": "set_capacitance",
        "temp_rtd": "set_temperature_rtd", "diod": "set_diode", "cont": "set_continuity",
    }
    return _map.get(mode_id, "set_voltage_dc")


class MeasureWorker(QThread):
    """Thread pour une mesure (évite de bloquer l'UI)."""
    result = pyqtSignal(str, float, str)  # raw, value_or_nan, unit
    secondary_value = pyqtSignal(str)  # valeur MEAS2? si demandé
    error = pyqtSignal(str)

    def __init__(self, measurement, unit: str = "V", read_secondary: bool = False):
        super().__init__()
        self._measurement = measurement
        self._unit = unit
        self._read_secondary = read_secondary

    def run(self):
        try:
            raw = self._measurement.read_value()
            val = self._measurement.parse_float(raw)
            if val is None:
                val = float("nan")
            self.result.emit(raw, val, self._unit)
            if self._read_secondary and hasattr(self._measurement, "read_secondary_value"):
                try:
                    sec = self._measurement.read_secondary_value()
                    self.secondary_value.emit(sec or "—")
                except Exception:
                    self.secondary_value.emit("—")
        except Exception as e:
            self.error.emit(str(e))


class MeterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._measurement = None
        self._history = []  # list of (value_str, unit)
        self._history_max = 100
        self._continuous_timer = QTimer(self)
        self._continuous_timer.timeout.connect(self._on_measure)
        self._continuous_interval_ms = 500
        self._build_ui()

    def set_measurement(self, measurement):
        """Injection de la couche mesure (depuis main_window)."""
        self._measurement = measurement
        if measurement:
            self._refresh_range_combo()

    def load_config(self, config: dict) -> None:
        """Intervalle de rafraîchissement, taille historique, et défauts mesure (vitesse, auto-plage)."""
        meas = config.get("measurement") or {}
        ms = meas.get("refresh_interval_ms", 500)
        self._continuous_interval_ms = max(100, min(5000, int(ms)))
        hist = (config.get("limits") or {}).get("history_size", 100)
        self._history_max = max(10, min(1000, int(hist)))
        if self._measurement:
            try:
                rate = (meas.get("default_rate") or "F").upper()
                if rate in ("F", "M", "L"):
                    self._measurement.set_rate(rate)
                    self._rate_selector.set_rate(rate)
                if meas.get("default_auto_range", True):
                    self._measurement.set_auto_range(True)
            except Exception:
                pass

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        layout = QVBoxLayout(content)

        self._mode_bar = ModeBar()
        self._mode_bar.mode_changed.connect(self._on_mode)
        layout.addWidget(self._mode_bar)

        self._display = MeasurementDisplay()
        self._display.secondary_display_toggled.connect(self._on_secondary_display_toggled)
        layout.addWidget(self._display)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        self._range_selector = RangeSelector()
        self._range_selector.auto_toggled.connect(self._on_range_auto_toggled)
        self._range_selector.range_changed.connect(self._on_range_selected)
        row_layout.addWidget(self._range_selector)
        self._rate_selector = RateSelector()
        self._rate_selector.rate_changed.connect(self._on_rate)
        row_layout.addWidget(self._rate_selector)
        self._math_panel = MathPanel()
        self._math_panel.math_changed.connect(self._on_math)
        self._math_panel.rel_offset_changed.connect(self._on_math_rel_changed)
        self._math_panel.db_ref_changed.connect(self._on_math_db_ref_changed)
        self._math_panel.reset_stats_clicked.connect(self._on_math_reset_stats)
        row_layout.addWidget(self._math_panel)
        layout.addWidget(row)

        self._advanced_params = AdvancedParamsPanel()
        self._advanced_params.rtd_type_changed.connect(self._on_rtd_type_changed)
        self._advanced_params.rtd_unit_changed.connect(self._on_rtd_unit_changed)
        self._advanced_params.rtd_show_changed.connect(self._on_rtd_show_changed)
        self._advanced_params.continuity_threshold_changed.connect(self._on_cont_thre_changed)
        self._advanced_params.buzzer_toggled.connect(self._on_buzzer_toggled)
        layout.addWidget(self._advanced_params)

        self._history_widget = HistoryTable()
        self._history_widget.clear_requested.connect(self._on_clear_history)
        self._history_widget.export_requested.connect(self._on_export_csv)
        layout.addWidget(self._history_widget)

        actions = QHBoxLayout()
        self._measure_btn = QPushButton("Mesure")
        self._measure_btn.clicked.connect(self._on_measure)
        actions.addWidget(self._measure_btn)
        self._continuous_btn = QPushButton("Mesure continue")
        self._continuous_btn.setCheckable(True)
        self._continuous_btn.clicked.connect(self._on_toggle_continuous)
        actions.addWidget(self._continuous_btn)
        self._reset_btn = QPushButton("Reset (*RST)")
        self._reset_btn.clicked.connect(self._on_reset)
        actions.addWidget(self._reset_btn)
        self._export_csv_btn = QPushButton("Exporter CSV")
        self._export_csv_btn.clicked.connect(self._on_export_csv)
        actions.addWidget(self._export_csv_btn)
        layout.addLayout(actions)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _on_mode(self, index: int):
        if not self._measurement or index < 0 or index >= len(MODE_IDS):
            return
        setter = getattr(self._measurement, _mode_setter_name(MODE_IDS[index]), None)
        if setter and callable(setter):
            try:
                setter()
            except Exception:
                pass
        self._refresh_range_combo()

    def _refresh_range_combo(self):
        if not self._measurement:
            return
        range_data = self._measurement.get_ranges_for_current_mode()
        self._range_selector.set_ranges(range_data)
        if range_data and not self._range_selector.is_auto():
            try:
                self._measurement.set_range(self._range_selector.get_value_at(0))
            except Exception:
                pass

    def _on_range_auto_toggled(self, checked: bool):
        if checked and self._measurement:
            try:
                self._measurement.set_auto_range(True)
            except Exception:
                pass

    def _on_range_selected(self, index: int):
        if not self._measurement or index < 0:
            return
        value = self._range_selector.get_value_at(index)
        if value is not None:
            try:
                self._measurement.set_range(value)
            except Exception:
                pass

    def _on_rate(self, rate: str):
        if self._measurement:
            try:
                self._measurement.set_rate(rate)
            except Exception:
                pass

    def _on_secondary_display_toggled(self, checked: bool):
        if self._measurement and hasattr(self._measurement, "set_secondary_display"):
            try:
                self._measurement.set_secondary_display(checked)
            except Exception:
                pass
        if not checked:
            self._display.set_secondary("—")

    def _on_math(self, key: str):
        if not self._measurement:
            return
        try:
            if key == "none":
                self._measurement.set_math_off()
            elif key == "rel":
                self._measurement.set_math_rel(self._math_panel.rel_offset())
            elif key == "db":
                self._measurement.set_math_db(self._math_panel.db_ref())
            elif key == "dbm":
                self._measurement.set_math_dbm(self._math_panel.db_ref())
            elif key == "avg":
                self._measurement.set_math_average()
        except Exception:
            pass

    def _on_math_rel_changed(self, value: float):
        if self._math_panel.current_math() == "rel" and self._measurement:
            try:
                self._measurement.set_math_rel(value)
            except Exception:
                pass

    def _on_math_db_ref_changed(self, ref: float):
        if not self._measurement:
            return
        try:
            if self._math_panel.current_math() == "db":
                self._measurement.set_math_db(ref)
            elif self._math_panel.current_math() == "dbm":
                self._measurement.set_math_dbm(ref)
        except Exception:
            pass

    def _on_math_reset_stats(self):
        if self._measurement and hasattr(self._measurement, "reset_stats"):
            try:
                self._measurement.reset_stats()
                self._refresh_math_stats()
            except Exception:
                pass

    def _refresh_math_stats(self):
        if not self._measurement or not self._math_panel.is_avg_checked():
            return
        try:
            s = self._measurement.get_stats()
            self._math_panel.set_stats(
                min_v=s.get("min"),
                max_v=s.get("max"),
                avg_v=s.get("avg"),
                n_v=s.get("n"),
            )
        except Exception:
            self._math_panel.set_stats_placeholder()

    def _on_rtd_type_changed(self, text: str):
        if self._measurement and hasattr(self._measurement, "set_rtd_type"):
            try:
                self._measurement.set_rtd_type(text or "KITS90")
            except Exception:
                pass

    def _on_rtd_unit_changed(self, unit: str):
        if self._measurement and hasattr(self._measurement, "set_rtd_unit"):
            try:
                self._measurement.set_rtd_unit(unit or "C")
            except Exception:
                pass

    def _on_rtd_show_changed(self, text: str):
        if self._measurement and hasattr(self._measurement, "set_rtd_show"):
            try:
                self._measurement.set_rtd_show(text or "TEMP")
            except Exception:
                pass

    def _on_cont_thre_changed(self, value: float):
        if self._measurement and hasattr(self._measurement, "set_continuity_threshold"):
            try:
                self._measurement.set_continuity_threshold(value)
            except Exception:
                pass

    def _on_buzzer_toggled(self, checked: bool):
        if self._measurement and hasattr(self._measurement, "set_buzzer"):
            try:
                self._measurement.set_buzzer(checked)
            except Exception:
                pass

    def _on_measure(self):
        if not self._measurement:
            self._display.set_value("—")
            return
        self._measure_btn.setEnabled(False)
        unit = self._measurement.get_unit_for_current_mode()
        read_secondary = self._display.is_secondary_visible()
        self._worker = MeasureWorker(self._measurement, unit, read_secondary=read_secondary)
        self._worker.result.connect(self._on_measure_result)
        self._worker.secondary_value.connect(self._display.set_secondary)
        self._worker.error.connect(self._on_measure_error)
        self._worker.finished.connect(lambda: self._measure_btn.setEnabled(True))
        self._worker.finished.connect(self._on_measure_finished)
        self._worker.start()

    def _on_measure_result(self, raw: str, value: float, unit: str):
        if value != value:  # nan
            text = raw.strip() or "—"
        else:
            text = f"{value:.4g} {unit}"
        self._display.set_value(text)
        self._history.append((text.split()[0] if value == value else raw, unit))
        if len(self._history) > self._history_max:
            self._history.pop(0)
        self._refresh_history_table()

    def _on_measure_finished(self):
        """Après une mesure : rafraîchir les stats si mode Moyenne."""
        self._refresh_math_stats()

    def _on_measure_error(self, msg: str):
        self._display.set_value("Err")
        QMessageBox.warning(self, "Mesure", f"Erreur : {msg}")

    def _refresh_history_table(self):
        self._history_widget.set_rows(self._history)

    def _on_clear_history(self):
        self._history.clear()

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

    def _on_toggle_continuous(self):
        if self._continuous_btn.isChecked():
            self._continuous_timer.start(self._continuous_interval_ms)
        else:
            self._continuous_timer.stop()

    def _on_reset(self):
        if self._measurement and hasattr(self._measurement, "reset"):
            try:
                self._measurement.reset()
            except Exception:
                pass

    # --- Raccourcis clavier (appelés par MainWindow lorsque l'onglet Multimètre est actif) ---

    def trigger_measure(self) -> None:
        """Déclenche une mesure unique (F5)."""
        self._on_measure()

    def toggle_continuous_measure(self) -> None:
        """Bascule mesure continue ON/OFF (Ctrl+M)."""
        self._continuous_btn.setChecked(not self._continuous_btn.isChecked())
        # _on_toggle_continuous est déjà appelé par le signal clicked du bouton
        self._on_toggle_continuous()

    def trigger_reset(self) -> None:
        """Envoie *RST au multimètre (Ctrl+R)."""
        self._on_reset()

    def trigger_export_csv(self) -> None:
        """Ouvre la boîte d'export CSV (Ctrl+E)."""
        self._on_export_csv()
