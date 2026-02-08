"""Panneau Ordonnée (Y) — choix gain linéaire / dB."""
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QRadioButton, QButtonGroup


def build_y_axis_panel(parent) -> QGroupBox:
    """Construit le groupbox Ordonnée (Y) et attache les widgets à parent."""
    gb = QGroupBox("Ordonnée (Y)")
    layout = QHBoxLayout(gb)
    parent._y_group = QButtonGroup(parent)
    parent._y_linear = QRadioButton("Gain linéaire (Us/Ue)")
    parent._y_db = QRadioButton("Gain en dB")
    parent._y_db.setChecked(True)
    parent._y_group.addButton(parent._y_linear)
    parent._y_group.addButton(parent._y_db)
    layout.addWidget(parent._y_linear)
    layout.addWidget(parent._y_db)
    layout.addStretch()
    return gb
