"""Panneau Échelles / Zoom — F min/max, Gain min/max, Appliquer, Zoom zone."""
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QDoubleSpinBox,
)


def build_scale_panel(parent, on_apply_scale, on_zoom_zone_toggled) -> QGroupBox:
    """Construit le groupbox Échelles / Zoom et attache les widgets à parent."""
    gb = QGroupBox("Échelles / Zoom")
    layout = QHBoxLayout(gb)
    layout.addWidget(QLabel("F min (Hz):"))
    parent._f_min_spin = QDoubleSpinBox()
    parent._f_min_spin.setRange(0.1, 1e9)
    parent._f_min_spin.setDecimals(2)
    parent._f_min_spin.setValue(10)
    parent._f_min_spin.setSingleStep(10)
    parent._f_min_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    layout.addWidget(parent._f_min_spin)
    layout.addWidget(QLabel("F max (Hz):"))
    parent._f_max_spin = QDoubleSpinBox()
    parent._f_max_spin.setRange(0.1, 1e9)
    parent._f_max_spin.setDecimals(2)
    parent._f_max_spin.setValue(100000)
    parent._f_max_spin.setSingleStep(1000)
    parent._f_max_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    layout.addWidget(parent._f_max_spin)
    layout.addWidget(QLabel("Gain min:"))
    parent._gain_min_spin = QDoubleSpinBox()
    parent._gain_min_spin.setRange(-300, 100)
    parent._gain_min_spin.setDecimals(2)
    parent._gain_min_spin.setValue(-50)
    parent._gain_min_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    layout.addWidget(parent._gain_min_spin)
    layout.addWidget(QLabel("Gain max:"))
    parent._gain_max_spin = QDoubleSpinBox()
    parent._gain_max_spin.setRange(-300, 100)
    parent._gain_max_spin.setDecimals(2)
    parent._gain_max_spin.setValue(5)
    parent._gain_max_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    layout.addWidget(parent._gain_max_spin)
    parent._apply_scale_btn = QPushButton("Appliquer les limites")
    parent._apply_scale_btn.setToolTip("Appliquer les valeurs ci-dessus aux axes du graphique")
    parent._apply_scale_btn.clicked.connect(on_apply_scale)
    layout.addWidget(parent._apply_scale_btn)
    parent._zoom_zone_cb = QCheckBox("Zoom sur zone (glisser)")
    parent._zoom_zone_cb.setToolTip(
        "Coché : glisser sur le graphique pour sélectionner une zone et zoomer. "
        "Décoché : glisser = déplacer la vue. Molette = zoom toujours actif."
    )
    parent._zoom_zone_cb.toggled.connect(on_zoom_zone_toggled)
    layout.addWidget(parent._zoom_zone_cb)
    layout.addStretch()
    return gb
