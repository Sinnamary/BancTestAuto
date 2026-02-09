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

        # === Entrées R, L, C ===
        params_gb = QGroupBox("Composants (entrée unique pour tous les filtres)")
        params_layout = QFormLayout(params_gb)

        self._r_spin = QDoubleSpinBox()
        self._r_spin.setRange(0.1, 10e6)
        self._r_spin.setValue(10000)
        self._r_spin.setDecimals(2)
        self._r_spin.setSuffix(" Ω")
        self._r_spin.setToolTip("Résistance en ohms")
        params_layout.addRow("R (résistance)", self._r_spin)

        self._l_spin = QDoubleSpinBox()
        self._l_spin.setRange(1e-9, 10)
        self._l_spin.setValue(0.001)
        self._l_spin.setDecimals(6)
        self._l_spin.setSuffix(" H")
        self._l_spin.setToolTip("Inductance (self) en henrys (ex. 0.001 = 1 mH)")
        params_layout.addRow("L (self / inductance)", self._l_spin)

        self._c_spin = QDoubleSpinBox()
        self._c_spin.setRange(1e-12, 0.01)
        self._c_spin.setValue(1e-6)
        self._c_spin.setDecimals(9)
        self._c_spin.setSuffix(" F")
        self._c_spin.setToolTip("Capacité en farads (ex. 1e-6 = 1 µF)")
        params_layout.addRow("C (condensateur)", self._c_spin)

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

    def _update_results(self):
        r = self._r_spin.value()
        l_val = self._l_spin.value()
        c = self._c_spin.value()

        self._result_labels["rc_lowpass"].setText(_format_freq(rc_passe_bas_fc(r, c)))
        self._result_labels["rc_highpass"].setText(_format_freq(rc_passe_haut_fc(r, c)))
        self._result_labels["wien"].setText(_format_freq(pont_wien_fc(r, c)))
        self._result_labels["rlc"].setText(_format_freq(rlc_resonance_fc(r, l_val, c)))
        self._result_labels["double_t"].setText(_format_freq(double_t_fc(r, c)))
