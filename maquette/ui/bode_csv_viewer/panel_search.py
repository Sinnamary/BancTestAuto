"""Panneau Recherche gain cible — saisie dB, Rechercher, Effacer."""
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
)


def build_search_panel(parent, on_search, on_clear) -> QGroupBox:
    """Construit le groupbox Recherche gain cible et attache les widgets à parent."""
    gb = QGroupBox("Recherche gain cible")
    layout = QHBoxLayout(gb)
    layout.addWidget(QLabel("Gain (dB):"))
    parent._target_gain_spin = QDoubleSpinBox()
    parent._target_gain_spin.setRange(-100, 50)
    parent._target_gain_spin.setDecimals(1)
    parent._target_gain_spin.setValue(-3)
    parent._target_gain_spin.setSingleStep(1)
    parent._target_gain_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    layout.addWidget(parent._target_gain_spin)
    parent._search_target_btn = QPushButton("Rechercher")
    parent._search_target_btn.setToolTip("Affiche les fréquences où la courbe coupe ce gain")
    parent._search_target_btn.clicked.connect(on_search)
    layout.addWidget(parent._search_target_btn)
    parent._clear_target_btn = QPushButton("Effacer la ligne")
    parent._clear_target_btn.setToolTip("Supprime la ligne de gain cible et les marqueurs de fréquence")
    parent._clear_target_btn.clicked.connect(on_clear)
    layout.addWidget(parent._clear_target_btn)
    parent._target_result_label = QLabel("")
    parent._target_result_label.setStyleSheet("color: gray; font-size: 10px;")
    layout.addWidget(parent._target_result_label)
    layout.addStretch()
    return gb
