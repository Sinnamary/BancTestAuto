"""Panneau boutons — Ajuster vue, Exporter PNG, Exporter CSV, Fermer."""
from PyQt6.QtWidgets import QHBoxLayout, QPushButton


def build_buttons_layout(parent, on_adjust, on_export_png, on_export_csv) -> QHBoxLayout:
    """Construit la rangée de boutons et attache les widgets à parent."""
    layout = QHBoxLayout()
    parent._adjust_btn = QPushButton("Ajuster vue")
    parent._adjust_btn.setToolTip("Recadrer la vue sur toutes les données")
    parent._adjust_btn.clicked.connect(on_adjust)
    layout.addWidget(parent._adjust_btn)
    layout.addStretch()
    parent._export_btn = QPushButton("Exporter en PNG")
    parent._export_btn.clicked.connect(on_export_png)
    layout.addWidget(parent._export_btn)
    parent._export_csv_btn = QPushButton("Exporter les points CSV")
    parent._export_csv_btn.setToolTip("Enregistre f_Hz, Us_V, Us_Ue, Gain_dB")
    parent._export_csv_btn.clicked.connect(on_export_csv)
    layout.addWidget(parent._export_csv_btn)
    parent._close_btn = QPushButton("Fermer")
    parent._close_btn.clicked.connect(parent.accept)
    layout.addWidget(parent._close_btn)
    return layout
