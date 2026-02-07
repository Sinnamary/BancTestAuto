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
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from core.measurement import MODE_IDS


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
        self._range_data = []  # [(label, value), ...] pour le combo plage
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

        modes_gb = QGroupBox("Modes de mesure")
        modes_layout = QHBoxLayout(modes_gb)
        modes_layout.setSpacing(4)
        self._mode_group = QButtonGroup(self)
        self._mode_buttons = []
        modes = ["V⎓", "V~", "A⎓", "A~", "Ω", "Ω 4W", "Hz", "s", "F", "°C", "⊿", "⚡"]
        _mode_btn_style = (
            "QPushButton { font-size: 11px; padding: 2px 6px; min-width: 32px; max-height: 22px; }"
        )
        for i, m in enumerate(modes):
            btn = QPushButton(m)
            btn.setCheckable(True)
            btn.setStyleSheet(_mode_btn_style)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda checked, idx=i: self._on_mode(idx))
            self._mode_group.addButton(btn)
            modes_layout.addWidget(btn)
            self._mode_buttons.append(btn)
        self._mode_buttons[0].setChecked(True)
        layout.addWidget(modes_gb)

        display_gb = QGroupBox("Affichage")
        display_layout = QHBoxLayout(display_gb)
        self._value_label = QLabel("—")
        self._value_label.setStyleSheet("font-size: 28px; font-family: Consolas, monospace;")
        self._value_label.setMinimumWidth(200)
        display_layout.addWidget(self._value_label)
        display_layout.addStretch()
        self._secondary_check = QCheckBox("Afficher Hz")
        self._secondary_check.toggled.connect(self._on_secondary_display_toggled)
        display_layout.addWidget(self._secondary_check)
        self._secondary_label = QLabel("—")
        self._secondary_label.setStyleSheet("font-size: 14px;")
        display_layout.addWidget(self._secondary_label)
        layout.addWidget(display_gb)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        range_gb = QGroupBox("Plage")
        range_layout = QVBoxLayout(range_gb)
        self._range_auto_radio = QRadioButton("Auto")
        self._range_auto_radio.setChecked(True)
        self._range_auto_radio.toggled.connect(self._on_range_auto_toggled)
        range_layout.addWidget(self._range_auto_radio)
        self._range_manual_radio = QRadioButton("Manuel")
        self._range_manual_radio.toggled.connect(self._on_range_manual_toggled)
        range_layout.addWidget(self._range_manual_radio)
        self._range_combo = QComboBox()
        self._range_combo.currentIndexChanged.connect(self._on_range_combo_changed)
        range_layout.addWidget(self._range_combo)
        row_layout.addWidget(range_gb)
        rate_gb = QGroupBox("Vitesse")
        rate_layout = QVBoxLayout(rate_gb)
        self._rate_group = QButtonGroup(self)
        self._rate_buttons = []
        for label, rate in (("Rapide", "F"), ("Moyenne", "M"), ("Lente", "L")):
            rb = QRadioButton(label)
            rb.clicked.connect(lambda checked, r=rate: self._on_rate(r))
            self._rate_group.addButton(rb)
            rate_layout.addWidget(rb)
            self._rate_buttons.append((rb, rate))
        self._rate_buttons[0][0].setChecked(True)
        row_layout.addWidget(rate_gb)
        math_gb = QGroupBox("Fonctions math")
        math_layout = QVBoxLayout(math_gb)
        self._math_group = QButtonGroup(self)
        self._math_radios = {}
        for label, key in (("Aucun", "none"), ("Rel", "rel"), ("dB", "db"), ("dBm", "dbm"), ("Moyenne", "avg")):
            rb = QRadioButton(label)
            rb.clicked.connect(lambda checked, k=key: self._on_math(k))
            self._math_group.addButton(rb)
            math_layout.addWidget(rb)
            self._math_radios[key] = rb
        self._math_rel_spin = QDoubleSpinBox()
        self._math_rel_spin.setRange(-1e12, 1e12)
        self._math_rel_spin.setDecimals(6)
        self._math_rel_spin.setValue(0)
        self._math_rel_spin.valueChanged.connect(self._on_math_rel_changed)
        math_layout.addWidget(QLabel("Rel offset:"))
        math_layout.addWidget(self._math_rel_spin)
        self._math_db_ref_combo = QComboBox()
        self._math_db_ref_combo.addItems([str(x) for x in (50, 75, 93, 110, 124, 125, 135, 150, 250, 300, 500, 600, 800, 900, 1000, 1200, 8000)])
        self._math_db_ref_combo.currentTextChanged.connect(self._on_math_db_ref_changed)
        math_layout.addWidget(QLabel("Réf. dB/dBm (Ω):"))
        math_layout.addWidget(self._math_db_ref_combo)
        self._math_stats_label = QLabel("Min: —  Max: —  Moy: —  N: —")
        self._math_stats_label.setStyleSheet("font-size: 11px; color: #888;")
        math_layout.addWidget(self._math_stats_label)
        self._math_reset_btn = QPushButton("Réinitialiser stats")
        self._math_reset_btn.clicked.connect(self._on_math_reset_stats)
        math_layout.addWidget(self._math_reset_btn)
        self._math_radios["none"].setChecked(True)
        row_layout.addWidget(math_gb)
        layout.addWidget(row)

        # Paramètres avancés (température, continuité, buzzer)
        adv_gb = QGroupBox("Paramètres avancés")
        adv_layout = QVBoxLayout(adv_gb)
        adv_layout.addWidget(QLabel("Température RTD:"))
        adv_row1 = QHBoxLayout()
        self._rtd_type_combo = QComboBox()
        self._rtd_type_combo.addItems(["KITS90", "PT100"])
        self._rtd_type_combo.currentTextChanged.connect(self._on_rtd_type_changed)
        adv_row1.addWidget(self._rtd_type_combo)
        self._rtd_unit_combo = QComboBox()
        self._rtd_unit_combo.addItems(["°C", "°F", "K"])
        self._rtd_unit_combo.currentTextChanged.connect(self._on_rtd_unit_changed)
        adv_row1.addWidget(self._rtd_unit_combo)
        self._rtd_show_combo = QComboBox()
        self._rtd_show_combo.addItems(["TEMP", "MEAS", "ALL"])
        self._rtd_show_combo.currentTextChanged.connect(self._on_rtd_show_changed)
        adv_row1.addWidget(self._rtd_show_combo)
        adv_layout.addLayout(adv_row1)
        adv_layout.addWidget(QLabel("Continuité seuil (Ω):"))
        self._cont_thre_spin = QDoubleSpinBox()
        self._cont_thre_spin.setRange(0.1, 10000)
        self._cont_thre_spin.setValue(10)
        self._cont_thre_spin.valueChanged.connect(self._on_cont_thre_changed)
        adv_layout.addWidget(self._cont_thre_spin)
        self._buzzer_check = QCheckBox("Buzzer ON")
        self._buzzer_check.toggled.connect(self._on_buzzer_toggled)
        adv_layout.addWidget(self._buzzer_check)
        layout.addWidget(adv_gb)

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

        self._export_hist_btn.clicked.connect(self._on_export_csv)
        self._clear_hist_btn.clicked.connect(self._on_clear_history)

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
        self._range_combo.blockSignals(True)
        self._range_combo.clear()
        self._range_data = self._measurement.get_ranges_for_current_mode()
        for label, _ in self._range_data:
            self._range_combo.addItem(label)
        self._range_combo.setEnabled(len(self._range_data) > 0 and self._range_manual_radio.isChecked())
        self._range_combo.blockSignals(False)
        if self._range_data and self._range_manual_radio.isChecked():
            try:
                self._measurement.set_range(self._range_data[0][1])
            except Exception:
                pass

    def _on_range_auto_toggled(self, checked: bool):
        if checked and self._measurement:
            try:
                self._measurement.set_auto_range(True)
            except Exception:
                pass
        self._range_combo.setEnabled(not checked and len(self._range_data) > 0)

    def _on_range_manual_toggled(self, checked: bool):
        self._range_combo.setEnabled(checked and len(self._range_data) > 0)
        if checked and self._measurement and self._range_data and self._range_combo.currentIndex() >= 0:
            idx = self._range_combo.currentIndex()
            if 0 <= idx < len(self._range_data):
                try:
                    self._measurement.set_range(self._range_data[idx][1])
                except Exception:
                    pass

    def _on_range_combo_changed(self, index: int):
        if not self._measurement or index < 0 or index >= len(self._range_data):
            return
        try:
            self._measurement.set_range(self._range_data[index][1])
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
            self._secondary_label.setText("—")

    def _on_math(self, key: str):
        if not self._measurement:
            return
        try:
            if key == "none":
                self._measurement.set_math_off()
            elif key == "rel":
                self._measurement.set_math_rel(self._math_rel_spin.value())
            elif key == "db":
                ref = float(self._math_db_ref_combo.currentText())
                self._measurement.set_math_db(ref)
            elif key == "dbm":
                ref = float(self._math_db_ref_combo.currentText())
                self._measurement.set_math_dbm(ref)
            elif key == "avg":
                self._measurement.set_math_average()
        except Exception:
            pass

    def _on_math_rel_changed(self, value: float):
        if self._math_radios.get("rel") and self._math_radios["rel"].isChecked() and self._measurement:
            try:
                self._measurement.set_math_rel(value)
            except Exception:
                pass

    def _on_math_db_ref_changed(self, text: str):
        if not text or not self._measurement:
            return
        try:
            ref = float(text)
            if self._math_radios.get("db") and self._math_radios["db"].isChecked():
                self._measurement.set_math_db(ref)
            elif self._math_radios.get("dbm") and self._math_radios["dbm"].isChecked():
                self._measurement.set_math_dbm(ref)
        except ValueError:
            pass

    def _on_math_reset_stats(self):
        if self._measurement and hasattr(self._measurement, "reset_stats"):
            try:
                self._measurement.reset_stats()
                self._refresh_math_stats()
            except Exception:
                pass

    def _refresh_math_stats(self):
        if not self._measurement or not (self._math_radios.get("avg") and self._math_radios["avg"].isChecked()):
            return
        try:
            s = self._measurement.get_stats()
            min_v = s.get("min")
            max_v = s.get("max")
            avg_v = s.get("avg")
            n_v = s.get("n")
            def _f(x):
                return f"{x:.4g}" if x is not None else "—"
            self._math_stats_label.setText(
                f"Min: {_f(min_v)}  Max: {_f(max_v)}  Moy: {_f(avg_v)}  N: {n_v if n_v is not None else '—'}"
            )
        except Exception:
            self._math_stats_label.setText("Min: —  Max: —  Moy: —  N: —")

    def _on_rtd_type_changed(self, text: str):
        if self._measurement and hasattr(self._measurement, "set_rtd_type"):
            try:
                self._measurement.set_rtd_type(text or "KITS90")
            except Exception:
                pass

    def _on_rtd_unit_changed(self, text: str):
        if self._measurement and hasattr(self._measurement, "set_rtd_unit"):
            try:
                u = "C"
                if text and "F" in text.upper():
                    u = "F"
                elif text and "K" in text.upper():
                    u = "K"
                self._measurement.set_rtd_unit(u)
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
            self._value_label.setText("—")
            return
        self._measure_btn.setEnabled(False)
        unit = self._measurement.get_unit_for_current_mode()
        read_secondary = self._secondary_check.isChecked()
        self._worker = MeasureWorker(self._measurement, unit, read_secondary=read_secondary)
        self._worker.result.connect(self._on_measure_result)
        self._worker.secondary_value.connect(self._secondary_label.setText)
        self._worker.error.connect(self._on_measure_error)
        self._worker.finished.connect(lambda: self._measure_btn.setEnabled(True))
        self._worker.finished.connect(self._on_measure_finished)
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

    def _on_measure_finished(self):
        """Après une mesure : rafraîchir les stats si mode Moyenne."""
        self._refresh_math_stats()

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
