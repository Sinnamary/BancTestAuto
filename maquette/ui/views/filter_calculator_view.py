"""
Onglet Calculateur de fréquence de coupure.
Saisie de R, L, C (et paramètres dédiés par filtre) pour calculer
les fréquences de coupure des principaux filtres : RC, CR, Pont de Wien, RLC, Double T.
Affiche un schéma par filtre et permet des paramètres avancés (ex. Pont de Wien R1,R2,C1,C2).
"""
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QFormLayout,
    QDoubleSpinBox,
    QComboBox,
    QScrollArea,
    QFrame,
    QCheckBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt

from core.app_paths import get_base_path
from core.filter_calculator import (
    rc_passe_bas_fc,
    rc_passe_haut_fc,
    pont_wien_fc,
    pont_wien_fc_general,
    rlc_resonance_fc,
    rlc_quality_factor,
    double_t_fc,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget
    HAS_SVG = True
except ImportError:
    try:
        from PyQt6.QtSvg import QSvgWidget
        HAS_SVG = True
    except ImportError:
        HAS_SVG = False


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

# Répertoire des schémas SVG des filtres
def _filters_resources_dir() -> Path:
    return get_base_path() / "resources" / "filters"


def _schema_widget(svg_name: str, size: int = 100) -> QWidget:
    """Crée un widget affichant le schéma SVG du filtre, ou un placeholder si SVG indisponible."""
    container = QFrame()
    container.setFrameStyle(QFrame.Shape.StyledPanel)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    path = _filters_resources_dir() / svg_name
    if HAS_SVG and path.exists():
        svg = QSvgWidget(str(path))
        svg.setFixedSize(size, int(size * 0.65))
        svg.setStyleSheet("background: white; border-radius: 4px;")
        layout.addWidget(svg, alignment=Qt.AlignmentFlag.AlignCenter)
    else:
        lbl = QLabel("Schéma\n" + svg_name.replace(".svg", "").replace("_", " ").title())
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFixedSize(size, int(size * 0.65))
        lbl.setStyleSheet("background: #f0f0f0; border-radius: 4px; font-size: 9px;")
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
    return container


class FilterCalculatorView(QWidget):
    """Vue pour le calcul des fréquences de coupure à partir de R, L, C et paramètres par filtre."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        self._update_results()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # === Composants globaux (valeurs par défaut pour tous les filtres) ===
        params_gb = QGroupBox("Composants par défaut (R, L, C)")
        params_layout = QFormLayout(params_gb)
        _spin_width = 100
        _combo_width = 60

        self._r_spin = QDoubleSpinBox()
        self._r_spin.setRange(0.0001, 1e10)
        self._r_spin.setValue(10)
        self._r_spin.setDecimals(4)
        self._r_spin.setMinimumWidth(_spin_width)
        self._r_combo = QComboBox()
        for label, _ in R_UNITS:
            self._r_combo.addItem(label)
        self._r_combo.setCurrentIndex(1)
        self._r_combo.setMinimumWidth(_combo_width)
        self._r_prev_unit_idx = 1
        row_r = QHBoxLayout()
        row_r.addWidget(self._r_spin)
        row_r.addWidget(self._r_combo)
        row_r.addStretch()
        params_layout.addRow("R (résistance)", row_r)

        self._l_spin = QDoubleSpinBox()
        self._l_spin.setRange(0, 1e10)
        self._l_spin.setValue(0)
        self._l_spin.setDecimals(4)
        self._l_spin.setMinimumWidth(_spin_width)
        self._l_combo = QComboBox()
        for label, _ in L_UNITS:
            self._l_combo.addItem(label)
        self._l_combo.setCurrentIndex(3)
        self._l_combo.setMinimumWidth(_combo_width)
        self._l_prev_unit_idx = 3
        row_l = QHBoxLayout()
        row_l.addWidget(self._l_spin)
        row_l.addWidget(self._l_combo)
        row_l.addStretch()
        params_layout.addRow("L (inductance)", row_l)

        self._c_spin = QDoubleSpinBox()
        self._c_spin.setRange(0, 1e10)
        self._c_spin.setValue(1)
        self._c_spin.setDecimals(4)
        self._c_spin.setMinimumWidth(_spin_width)
        self._c_combo = QComboBox()
        for label, _ in C_UNITS:
            self._c_combo.addItem(label)
        self._c_combo.setCurrentIndex(2)
        self._c_combo.setMinimumWidth(_combo_width)
        self._c_prev_unit_idx = 2
        row_c = QHBoxLayout()
        row_c.addWidget(self._c_spin)
        row_c.addWidget(self._c_combo)
        row_c.addStretch()
        params_layout.addRow("C (condensateur)", row_c)

        main_layout.addWidget(params_gb)

        # === Zone scrollable : un bloc par filtre (schéma + résultat + paramètres optionnels) ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        schema_size = 110

        # ---- RC passe-bas ----
        self._result_rc_lowpass = QLabel("—")
        self._result_rc_lowpass.setStyleSheet("font-weight: 600; min-width: 100px;")
        self._block_rc_lowpass = self._filter_block(
            "RC passe-bas",
            "rc_passe_bas.svg",
            "fc = 1 / (2π R C)",
            self._result_rc_lowpass,
            schema_size,
        )
        scroll_layout.addWidget(self._block_rc_lowpass)

        # ---- RC passe-haut ----
        self._result_rc_highpass = QLabel("—")
        self._result_rc_highpass.setStyleSheet("font-weight: 600; min-width: 100px;")
        self._block_rc_highpass = self._filter_block(
            "RC passe-haut (CR)",
            "rc_passe_haut.svg",
            "fc = 1 / (2π R C)",
            self._result_rc_highpass,
            schema_size,
        )
        scroll_layout.addWidget(self._block_rc_highpass)

        # ---- Pont de Wien (avec paramètres dédiés R1, R2, C1, C2) ----
        self._result_wien = QLabel("—")
        self._result_wien.setStyleSheet("font-weight: 600; min-width: 100px;")
        self._wien_use_dedicated = QCheckBox("Utiliser R1, R2, C1, C2 dédiés")
        self._wien_use_dedicated.setChecked(False)
        wien_extra = QWidget()
        wien_extra_layout = QFormLayout(wien_extra)
        self._wien_r1 = QDoubleSpinBox()
        self._wien_r1.setRange(0.0001, 1e10)
        self._wien_r1.setValue(10)
        self._wien_r1.setDecimals(4)
        self._wien_r1.setMinimumWidth(90)
        self._wien_r1_combo = QComboBox()
        for label, _ in R_UNITS:
            self._wien_r1_combo.addItem(label)
        self._wien_r1_combo.setCurrentIndex(1)
        row_wr1 = QHBoxLayout()
        row_wr1.addWidget(self._wien_r1)
        row_wr1.addWidget(self._wien_r1_combo)
        wien_extra_layout.addRow("R1", row_wr1)
        self._wien_r2 = QDoubleSpinBox()
        self._wien_r2.setRange(0.0001, 1e10)
        self._wien_r2.setValue(10)
        self._wien_r2.setDecimals(4)
        self._wien_r2_combo = QComboBox()
        for label, _ in R_UNITS:
            self._wien_r2_combo.addItem(label)
        self._wien_r2_combo.setCurrentIndex(1)
        row_wr2 = QHBoxLayout()
        row_wr2.addWidget(self._wien_r2)
        row_wr2.addWidget(self._wien_r2_combo)
        wien_extra_layout.addRow("R2", row_wr2)
        self._wien_c1 = QDoubleSpinBox()
        self._wien_c1.setRange(0, 1e10)
        self._wien_c1.setValue(1)
        self._wien_c1.setDecimals(4)
        self._wien_c1_combo = QComboBox()
        for label, _ in C_UNITS:
            self._wien_c1_combo.addItem(label)
        self._wien_c1_combo.setCurrentIndex(2)
        row_wc1 = QHBoxLayout()
        row_wc1.addWidget(self._wien_c1)
        row_wc1.addWidget(self._wien_c1_combo)
        wien_extra_layout.addRow("C1", row_wc1)
        self._wien_c2 = QDoubleSpinBox()
        self._wien_c2.setRange(0, 1e10)
        self._wien_c2.setValue(1)
        self._wien_c2_combo = QComboBox()
        for label, _ in C_UNITS:
            self._wien_c2_combo.addItem(label)
        self._wien_c2_combo.setCurrentIndex(2)
        row_wc2 = QHBoxLayout()
        row_wc2.addWidget(self._wien_c2)
        row_wc2.addWidget(self._wien_c2_combo)
        wien_extra_layout.addRow("C2", row_wc2)
        self._wien_extra_container = wien_extra
        self._wien_extra_container.setVisible(False)
        self._wien_use_dedicated.toggled.connect(self._wien_extra_container.setVisible)

        wien_right = QVBoxLayout()
        wien_right.addWidget(QLabel("fc = 1 / (2π √(R1 R2 C1 C2))"))
        wien_right.addWidget(self._result_wien)
        wien_right.addWidget(self._wien_use_dedicated)
        wien_right.addWidget(self._wien_extra_container)

        self._block_wien = self._filter_block(
            "Pont de Wien",
            "pont_wien.svg",
            "",
            None,
            schema_size,
            right_layout=wien_right,
        )
        scroll_layout.addWidget(self._block_wien)

        # ---- RLC (résonance + facteur Q) ----
        self._result_rlc = QLabel("—")
        self._result_rlc.setStyleSheet("font-weight: 600; min-width: 100px;")
        self._result_rlc_q = QLabel("—")
        rlc_right = QVBoxLayout()
        rlc_right.addWidget(QLabel("f0 = 1 / (2π √(L C))"))
        rlc_right.addWidget(QLabel("Fréquence :"))
        rlc_right.addWidget(self._result_rlc)
        rlc_right.addWidget(QLabel("Facteur de qualité Q :"))
        rlc_right.addWidget(self._result_rlc_q)
        self._block_rlc = self._filter_block(
            "RLC (résonance)",
            "rlc_resonance.svg",
            "",
            None,
            schema_size,
            right_layout=rlc_right,
        )
        scroll_layout.addWidget(self._block_rlc)

        # ---- Double T ----
        self._result_double_t = QLabel("—")
        self._result_double_t.setStyleSheet("font-weight: 600; min-width: 100px;")
        self._block_double_t = self._filter_block(
            "Double T (Twin-T)",
            "double_t.svg",
            "fc = 1 / (2π R C)",
            self._result_double_t,
            schema_size,
        )
        scroll_layout.addWidget(self._block_double_t)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _filter_block(
        self,
        title: str,
        svg_name: str,
        formula: str,
        result_label: QLabel | None,
        schema_size: int,
        right_layout: QVBoxLayout | None = None,
    ) -> QGroupBox:
        """Construit un groupe : schéma à gauche, formule + résultat à droite."""
        gb = QGroupBox(title)
        layout = QHBoxLayout(gb)
        layout.addWidget(_schema_widget(svg_name, schema_size))
        if right_layout is not None:
            right_w = QWidget()
            right_w.setLayout(right_layout)
            layout.addWidget(right_w, 1)
        else:
            layout.addWidget(QLabel(formula))
            if result_label is not None:
                layout.addWidget(result_label)
            layout.addStretch()
        return gb

    def _connect_signals(self):
        self._r_spin.valueChanged.connect(self._update_results)
        self._l_spin.valueChanged.connect(self._update_results)
        self._c_spin.valueChanged.connect(self._update_results)
        self._r_combo.currentIndexChanged.connect(self._on_r_unit_changed)
        self._l_combo.currentIndexChanged.connect(self._on_l_unit_changed)
        self._c_combo.currentIndexChanged.connect(self._on_c_unit_changed)
        self._wien_use_dedicated.toggled.connect(self._update_results)
        for w in (
            self._wien_r1,
            self._wien_r2,
            self._wien_c1,
            self._wien_c2,
        ):
            w.valueChanged.connect(self._update_results)
        self._wien_r1_combo.currentIndexChanged.connect(self._update_results)
        self._wien_r2_combo.currentIndexChanged.connect(self._update_results)
        self._wien_c1_combo.currentIndexChanged.connect(self._update_results)
        self._wien_c2_combo.currentIndexChanged.connect(self._update_results)

    def _get_r_si(self) -> float:
        return self._r_spin.value() * R_UNITS[self._r_combo.currentIndex()][1]

    def _get_l_si(self) -> float:
        return self._l_spin.value() * L_UNITS[self._l_combo.currentIndex()][1]

    def _get_c_si(self) -> float:
        return self._c_spin.value() * C_UNITS[self._c_combo.currentIndex()][1]

    def _get_wien_r1_si(self) -> float:
        return self._wien_r1.value() * R_UNITS[self._wien_r1_combo.currentIndex()][1]

    def _get_wien_r2_si(self) -> float:
        return self._wien_r2.value() * R_UNITS[self._wien_r2_combo.currentIndex()][1]

    def _get_wien_c1_si(self) -> float:
        return self._wien_c1.value() * C_UNITS[self._wien_c1_combo.currentIndex()][1]

    def _get_wien_c2_si(self) -> float:
        return self._wien_c2.value() * C_UNITS[self._wien_c2_combo.currentIndex()][1]

    def _on_r_unit_changed(self):
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

        self._result_rc_lowpass.setText(_format_freq(rc_passe_bas_fc(r, c)))
        self._result_rc_highpass.setText(_format_freq(rc_passe_haut_fc(r, c)))

        if self._wien_use_dedicated.isChecked():
            wien_fc = pont_wien_fc_general(
                self._get_wien_r1_si(),
                self._get_wien_r2_si(),
                self._get_wien_c1_si(),
                self._get_wien_c2_si(),
            )
        else:
            wien_fc = pont_wien_fc(r, c)
        self._result_wien.setText(_format_freq(wien_fc))

        self._result_rlc.setText(_format_freq(rlc_resonance_fc(r, l_val, c)))
        q_val = rlc_quality_factor(r, l_val, c)
        self._result_rlc_q.setText(f"{q_val:.4g}" if q_val is not None else "—")

        self._result_double_t.setText(_format_freq(double_t_fc(r, c)))
