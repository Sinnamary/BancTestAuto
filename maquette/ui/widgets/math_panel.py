"""
Panneau fonctions math : Aucun, Rel, dB, dBm, Moyenne + champs (offset, réf. Ω, stats).
Émet math_changed(key), rel_offset_changed(value), db_ref_changed(value), reset_stats_clicked().
"""
from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
)
from PyQt6.QtCore import pyqtSignal

DB_REF_OHMS = (50, 75, 93, 110, 124, 125, 135, 150, 250, 300, 500, 600, 800, 900, 1000, 1200, 8000)


class MathPanel(QGroupBox):
    """Fonctions math (Rel, dB, dBm, Moyenne) + offset, réf. Ω, stats."""

    math_changed = pyqtSignal(str)           # "none", "rel", "db", "dbm", "avg"
    rel_offset_changed = pyqtSignal(float)
    db_ref_changed = pyqtSignal(float)
    reset_stats_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Fonctions math", parent)
        self._radios = {}  # key -> QRadioButton
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self._group = QButtonGroup(self)
        for label, key in (("Aucun", "none"), ("Rel", "rel"), ("dB", "db"), ("dBm", "dbm"), ("Moyenne", "avg")):
            rb = QRadioButton(label)
            rb.clicked.connect(lambda checked, k=key: self.math_changed.emit(k))
            self._group.addButton(rb)
            layout.addWidget(rb)
            self._radios[key] = rb

        self._rel_spin = QDoubleSpinBox()
        self._rel_spin.setRange(-1e12, 1e12)
        self._rel_spin.setDecimals(6)
        self._rel_spin.setValue(0)
        self._rel_spin.valueChanged.connect(self.rel_offset_changed.emit)
        layout.addWidget(QLabel("Rel offset:"))
        layout.addWidget(self._rel_spin)

        self._db_ref_combo = QComboBox()
        self._db_ref_combo.addItems([str(x) for x in DB_REF_OHMS])
        self._db_ref_combo.currentTextChanged.connect(self._on_db_ref_text)
        layout.addWidget(QLabel("Réf. dB/dBm (Ω):"))
        layout.addWidget(self._db_ref_combo)

        self._stats_label = QLabel("Min: —  Max: —  Moy: —  N: —")
        self._stats_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self._stats_label)

        self._reset_btn = QPushButton("Réinitialiser stats")
        self._reset_btn.clicked.connect(self.reset_stats_clicked.emit)
        layout.addWidget(self._reset_btn)

        self._radios["none"].setChecked(True)

    def _on_db_ref_text(self, text: str):
        if text:
            try:
                self.db_ref_changed.emit(float(text))
            except ValueError:
                pass

    def current_math(self) -> str:
        for key, rb in self._radios.items():
            if rb.isChecked():
                return key
        return "none"

    def rel_offset(self) -> float:
        return self._rel_spin.value()

    def db_ref(self) -> float:
        try:
            return float(self._db_ref_combo.currentText())
        except ValueError:
            return 50.0

    def is_avg_checked(self) -> bool:
        return self._radios.get("avg") and self._radios["avg"].isChecked()

    def set_stats(self, min_v=None, max_v=None, avg_v=None, n_v=None) -> None:
        def _f(x):
            return f"{x:.4g}" if x is not None else "—"
        n_str = n_v if n_v is not None else "—"
        self._stats_label.setText(
            f"Min: {_f(min_v)}  Max: {_f(max_v)}  Moy: {_f(avg_v)}  N: {n_str}"
        )

    def set_stats_placeholder(self) -> None:
        """Affiche les tirets quand pas de stats."""
        self._stats_label.setText("Min: —  Max: —  Moy: —  N: —")
