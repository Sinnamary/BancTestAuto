"""Panneau Affichage — fond, couleur courbe, quadrillage, lissage, pics."""
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QLabel,
)

from .view_state import BodeViewOptions
from .smoothing import has_savgol


def build_display_panel(parent, on_options_changed) -> QGroupBox:
    """Construit le groupbox Affichage et attache les widgets à parent."""
    gb = QGroupBox("Affichage")
    layout = QHBoxLayout(gb)
    layout.addWidget(QLabel("Fond:"))
    parent._background_combo = QComboBox()
    for label, dark in BodeViewOptions.BACKGROUND_CHOICES:
        parent._background_combo.addItem(label, dark)
    parent._background_combo.setCurrentIndex(0 if parent._options.plot_background_dark else 1)
    parent._background_combo.currentIndexChanged.connect(on_options_changed)
    layout.addWidget(parent._background_combo)
    layout.addWidget(QLabel("Couleur courbe:"))
    parent._curve_color_combo = QComboBox()
    for label, hex_color in BodeViewOptions.CURVE_COLOR_CHOICES:
        parent._curve_color_combo.addItem(label, hex_color)
    parent._curve_color_combo.currentIndexChanged.connect(on_options_changed)
    layout.addWidget(parent._curve_color_combo)
    parent._grid_cb = QCheckBox("Quadrillage")
    parent._grid_cb.setChecked(True)
    parent._grid_cb.toggled.connect(on_options_changed)
    layout.addWidget(parent._grid_cb)
    parent._grid_minor_cb = QCheckBox("Quadrillage mineur")
    parent._grid_minor_cb.setToolTip("Lignes intermédiaires pour lecture fine")
    parent._grid_minor_cb.toggled.connect(on_options_changed)
    layout.addWidget(parent._grid_minor_cb)
    parent._smooth_cb = QCheckBox("Lissage")
    parent._smooth_cb.toggled.connect(on_options_changed)
    layout.addWidget(parent._smooth_cb)
    layout.addWidget(QLabel("Fenêtre:"))
    parent._smooth_combo = QComboBox()
    for w in BodeViewOptions.SMOOTH_WINDOW_CHOICES:
        parent._smooth_combo.addItem(str(w), w)
    parent._smooth_combo.setCurrentIndex(1)
    parent._smooth_combo.currentIndexChanged.connect(on_options_changed)
    layout.addWidget(parent._smooth_combo)
    layout.addWidget(QLabel("Algo:"))
    parent._smooth_method_combo = QComboBox()
    for label, use_savgol in BodeViewOptions.SMOOTH_METHODS:
        if use_savgol and not has_savgol():
            continue
        parent._smooth_method_combo.addItem(label, use_savgol)
    parent._smooth_method_combo.currentIndexChanged.connect(on_options_changed)
    layout.addWidget(parent._smooth_method_combo)
    parent._raw_cb = QCheckBox("Courbe brute + lissée")
    parent._raw_cb.toggled.connect(on_options_changed)
    layout.addWidget(parent._raw_cb)
    parent._peaks_cb = QCheckBox("Pics/creux")
    parent._peaks_cb.setToolTip("Marqueurs sur les maxima et minima locaux")
    parent._peaks_cb.toggled.connect(on_options_changed)
    layout.addWidget(parent._peaks_cb)
    layout.addStretch()
    return gb
