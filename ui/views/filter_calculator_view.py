"""
Onglet Calculateur de fréquence de coupure.
Saisie de R (résistance), L (self/inductance), C (condensateur) pour calculer
les fréquences de coupure des principaux filtres : RC, CR, Pont de Wien, RLC, Double T.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QFormLayout,
    QDoubleSpinBox,
    QComboBox,
)

from core.filter_calculator import (
    rc_passe_bas_fc,
    rc_passe_haut_fc,
    pont_wien_fc,
    rlc_resonance_fc,
    double_t_fc,
)


def _format_freq(hz: float | None) -> str:
    """Formate la fréquence en Hz avec unité adaptée (Hz, kHz, MHz)."""
    if hz is None or hz <= 0:
        return "—"
    if hz >= 1e6:
        return f"{hz / 1e6:.4g} MHz"
    if hz >= 1e3:
        return f"{hz / 1e3:.4g} kHz"
    return f"{hz:.4g} Hz"


# Facteurs de conversion vers unités SI (Ω, H, F)
R_UNITS = [("Ω", 1.0), ("kΩ", 1e3), ("MΩ", 1e6)]
L_UNITS = [("pH", 1e-12), ("nH", 1e-9), ("µH", 1e-6), ("mH", 1e-3), ("H", 1.0)]
C_UNITS = [("pF", 1e-12), ("nF", 1e-9), ("µF", 1e-6), ("mF", 1e-3), ("F", 1.0)]


class FilterCalculatorView(QWidget):
    """Vue pour le calcul des fréquences de coupure à partir de R, L, C."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        self._update_results()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # === Entrées R, L, C (valeur + unité) ===
        params_gb = QGroupBox("Composants (entrée unique pour tous les filtres)")
        params_layout = QFormLayout(params_gb)

        _spin_width = 100
        _combo_width = 60

        # R : spin + combo Ω / kΩ / MΩ
        self._r_spin = QDoubleSpinBox()
        self._r_spin.setRange(0.0001, 1e10)
        self._r_spin.setValue(10)
        self._r_spin.setDecimals(4)
        self._r_spin.setMinimumWidth(_spin_width)
        self._r_combo = QComboBox()
        for label, _ in R_UNITS:
            self._r_combo.addItem(label)
        self._r_combo.setCurrentIndex(1)  # kΩ par défaut
        self._r_combo.setMinimumWidth(_combo_width)
        self._r_prev_unit_idx = 1
        row_r = QHBoxLayout()
        row_r.addWidget(self._r_spin)
        row_r.addWidget(self._r_combo)
        row_r.addStretch()
        params_layout.addRow("R (résistance)", row_r)

        # L : spin + combo pH / nH / µH / mH / H
        self._l_spin = QDoubleSpinBox()
        self._l_spin.setRange(0, 1e10)
        self._l_spin.setValue(0)
        self._l_spin.setDecimals(4)
        self._l_spin.setMinimumWidth(_spin_width)
        self._l_combo = QComboBox()
        for label, _ in L_UNITS:
            self._l_combo.addItem(label)
        self._l_combo.setCurrentIndex(3)  # mH par défaut
        self._l_combo.setMinimumWidth(_combo_width)
        self._l_prev_unit_idx = 3
        row_l = QHBoxLayout()
        row_l.addWidget(self._l_spin)
        row_l.addWidget(self._l_combo)
        row_l.addStretch()
        params_layout.addRow("L (self / inductance)", row_l)

        # C : spin + combo pF / nF / µF / mF / F
        self._c_spin = QDoubleSpinBox()
        self._c_spin.setRange(0, 1e10)
        self._c_spin.setValue(1)
        self._c_spin.setDecimals(4)
        self._c_spin.setMinimumWidth(_spin_width)
        self._c_combo = QComboBox()
        for label, _ in C_UNITS:
            self._c_combo.addItem(label)
        self._c_combo.setCurrentIndex(2)  # µF par défaut
        self._c_combo.setMinimumWidth(_combo_width)
        self._c_prev_unit_idx = 2
        row_c = QHBoxLayout()
        row_c.addWidget(self._c_spin)
        row_c.addWidget(self._c_combo)
        row_c.addStretch()
        params_layout.addRow("C (condensateur)", row_c)

        layout.addWidget(params_gb)

        # === Résultats ===
        results_gb = QGroupBox("Fréquences de coupure calculées")
        results_layout = QFormLayout(results_gb)
        self._result_labels = {}

        filters = [
            ("RC passe-bas", "rc_lowpass", "fc = 1 / (2π R C)"),
            ("RC passe-haut (CR)", "rc_highpass", "fc = 1 / (2π R C)"),
            ("Pont de Wien", "wien", "fc = 1 / (2π R C)"),
            ("RLC (résonance)", "rlc", "f0 = 1 / (2π √(L C))"),
            ("Double T (Twin-T)", "double_t", "fc = 1 / (2π R C)"),
        ]
        for name, key, formula in filters:
            row = QHBoxLayout()
            lbl = QLabel("—")
            lbl.setMinimumWidth(120)
            lbl.setStyleSheet("font-weight: 600;")
            self._result_labels[key] = lbl
            row.addWidget(lbl)
            row.addWidget(QLabel(formula))
            row.addStretch()
            results_layout.addRow(name + " :", row)

        layout.addWidget(results_gb)
        layout.addStretch()

    def _connect_signals(self):
        self._r_spin.valueChanged.connect(self._update_results)
        self._l_spin.valueChanged.connect(self._update_results)
        self._c_spin.valueChanged.connect(self._update_results)
        self._r_combo.currentIndexChanged.connect(self._on_r_unit_changed)
        self._l_combo.currentIndexChanged.connect(self._on_l_unit_changed)
        self._c_combo.currentIndexChanged.connect(self._on_c_unit_changed)

    def _get_r_si(self) -> float:
        return self._r_spin.value() * R_UNITS[self._r_combo.currentIndex()][1]

    def _get_l_si(self) -> float:
        return self._l_spin.value() * L_UNITS[self._l_combo.currentIndex()][1]

    def _get_c_si(self) -> float:
        return self._c_spin.value() * C_UNITS[self._c_combo.currentIndex()][1]

    def _on_r_unit_changed(self):
        """Lors du changement d'unité, convertir la valeur affichée pour préserver la valeur SI."""
        prev = self._r_prev_unit_idx
        si = self._r_spin.value() * R_UNITS[prev][1]
        self._r_prev_unit_idx = self._r_combo.currentIndex()
        mult = R_UNITS[self._r_combo.currentIndex()][1]
        self._r_spin.blockSignals(True)
        self._r_spin.setValue(si / mult if mult else 0)
        self._r_spin.blockSignals(False)
        self._update_results()

    def _on_l_unit_changed(self):
        prev = self._l_prev_unit_idx
        si = self._l_spin.value() * L_UNITS[prev][1]
        self._l_prev_unit_idx = self._l_combo.currentIndex()
        mult = L_UNITS[self._l_combo.currentIndex()][1]
        self._l_spin.blockSignals(True)
        self._l_spin.setValue(si / mult if mult else 0)
        self._l_spin.blockSignals(False)
        self._update_results()

    def _on_c_unit_changed(self):
        prev = self._c_prev_unit_idx
        si = self._c_spin.value() * C_UNITS[prev][1]
        self._c_prev_unit_idx = self._c_combo.currentIndex()
        mult = C_UNITS[self._c_combo.currentIndex()][1]
        self._c_spin.blockSignals(True)
        self._c_spin.setValue(si / mult if mult else 0)
        self._c_spin.blockSignals(False)
        self._update_results()

    def _update_results(self):
        r = self._get_r_si()
        l_val = self._get_l_si()
        c = self._get_c_si()

        self._result_labels["rc_lowpass"].setText(_format_freq(rc_passe_bas_fc(r, c)))
        self._result_labels["rc_highpass"].setText(_format_freq(rc_passe_haut_fc(r, c)))
        self._result_labels["wien"].setText(_format_freq(pont_wien_fc(r, c)))
        self._result_labels["rlc"].setText(_format_freq(rlc_resonance_fc(r, l_val, c)))
        self._result_labels["double_t"].setText(_format_freq(double_t_fc(r, c)))
