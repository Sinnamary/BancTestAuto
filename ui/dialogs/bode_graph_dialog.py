"""
Fenêtre dédiée au graphique Bode : affiche la courbe de réponse en fréquence
avec choix de l'échelle en ordonnée (gain linéaire ou dB), quadrillage,
lissage, points significatifs (fc -3 dB) et export PNG.
Ouverte après un balayage ou via Fichier → Ouvrir CSV Banc filtre.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QPushButton,
    QCheckBox,
    QComboBox,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

try:
    from ui.views.bode_plot_widget import BodePlotWidget
    _BODE_PLOT_AVAILABLE = True
except ImportError:
    _BODE_PLOT_AVAILABLE = False
    BodePlotWidget = None


class BodeGraphDialog(QDialog):
    """Fenêtre affichant le graphique Bode avec options d'affichage et export."""

    def __init__(self, parent=None, points=None):
        super().__init__(parent)
        self._points = list(points) if points else []
        self.setWindowTitle("Graphique Bode — Banc filtre")
        self.setMinimumSize(640, 480)
        self.resize(800, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        y_axis_gb = QGroupBox("Ordonnée (Y) — échelle du gain")
        y_axis_layout = QHBoxLayout(y_axis_gb)
        self._y_axis_group = QButtonGroup(self)
        self._y_linear = QRadioButton("Gain linéaire (Us/Ue)")
        self._y_db = QRadioButton("Gain en dB")
        self._y_db.setChecked(True)
        self._y_axis_group.addButton(self._y_linear)
        self._y_axis_group.addButton(self._y_db)
        y_radio_style = (
            "QRadioButton { font-size: 11pt; font-weight: 500; padding: 8px 12px; min-height: 1.2em; } "
            "QRadioButton::indicator { width: 18px; height: 18px; } "
            "QRadioButton:checked { font-weight: 700; color: #ffc107; }"
        )
        self._y_linear.setStyleSheet(y_radio_style)
        self._y_db.setStyleSheet(y_radio_style)
        self._y_linear.setToolTip("Afficher le gain en valeur linéaire Us/Ue sur l'axe Y")
        self._y_db.setToolTip("Afficher le gain en décibels (20×log₁₀(Us/Ue)) sur l'axe Y")
        y_axis_layout.addWidget(self._y_linear)
        y_axis_layout.addWidget(self._y_db)
        y_axis_layout.addStretch()
        layout.addWidget(y_axis_gb)

        display_gb = QGroupBox("Affichage")
        display_layout = QHBoxLayout(display_gb)
        self._grid_cb = QCheckBox("Quadrillage")
        self._grid_cb.setChecked(True)
        self._grid_cb.setToolTip("Afficher la grille de référence sur le graphique")
        self._grid_cb.toggled.connect(self._on_display_changed)
        display_layout.addWidget(self._grid_cb)

        self._smooth_cb = QCheckBox("Lissage")
        self._smooth_cb.setToolTip("Lisser la courbe par moyenne glissante pour réduire le bruit")
        self._smooth_cb.toggled.connect(self._on_display_changed)
        display_layout.addWidget(self._smooth_cb)
        self._smooth_combo = QComboBox()
        for w in (3, 5, 7, 9, 11):
            self._smooth_combo.addItem(str(w), w)
        self._smooth_combo.setCurrentIndex(1)  # 5
        self._smooth_combo.setToolTip("Fenêtre de lissage (nombre de points)")
        self._smooth_combo.currentIndexChanged.connect(self._on_display_changed)
        display_layout.addWidget(QLabel("Fenêtre:"))
        display_layout.addWidget(self._smooth_combo)
        self._raw_curve_cb = QCheckBox("Courbe brute + lissée")
        self._raw_curve_cb.setToolTip("Afficher la courbe brute en gris en plus de la courbe lissée")
        self._raw_curve_cb.toggled.connect(self._on_display_changed)
        display_layout.addWidget(self._raw_curve_cb)

        self._points_cb = QCheckBox("Points significatifs (fc -3 dB)")
        self._points_cb.setChecked(True)
        self._points_cb.setToolTip("Afficher la fréquence de coupure à -3 dB")
        self._points_cb.toggled.connect(self._on_display_changed)
        display_layout.addWidget(self._points_cb)
        display_layout.addStretch()
        layout.addWidget(display_gb)

        if _BODE_PLOT_AVAILABLE and BodePlotWidget:
            self._bode_plot = BodePlotWidget()
            self._bode_plot.setMinimumHeight(280)
            layout.addWidget(self._bode_plot)
            self._plot_available = True
        else:
            self._bode_plot = None
            self._plot_available = False
            no_plot = QLabel("pyqtgraph requis pour afficher le graphique.")
            no_plot.setStyleSheet("color: #888; padding: 20px;")
            layout.addWidget(no_plot)

        btn_layout = QHBoxLayout()
        self._adjust_btn = QPushButton("Ajuster vue")
        self._adjust_btn.setToolTip("Recadrer la vue sur toutes les données")
        self._adjust_btn.clicked.connect(self._on_adjust_view)
        if not self._plot_available:
            self._adjust_btn.setEnabled(False)
        btn_layout.addWidget(self._adjust_btn)
        btn_layout.addStretch()
        self._export_btn = QPushButton("Exporter en PNG")
        self._export_btn.clicked.connect(self._on_export)
        if not self._plot_available:
            self._export_btn.setEnabled(False)
        btn_layout.addWidget(self._export_btn)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._y_linear.toggled.connect(self._on_y_axis_changed)
        self._y_db.toggled.connect(self._on_y_axis_changed)

        if self._points and self._bode_plot:
            self._bode_plot.set_bode_points(self._points, y_linear=self._y_linear.isChecked())
            self._on_display_changed()

    def _on_display_changed(self):
        if not self._bode_plot or not self._points:
            return
        self._bode_plot.set_show_grid(self._grid_cb.isChecked())
        if self._smooth_cb.isChecked():
            window = self._smooth_combo.currentData()
            if window is None:
                window = 5
            self._bode_plot.set_smoothing(
                window,
                show_raw_curve=self._raw_curve_cb.isChecked(),
            )
        else:
            self._bode_plot.set_smoothing(0, show_raw_curve=False)
        if self._points_cb.isChecked():
            res = self._bode_plot.get_cutoff_3db()
            if res:
                fc_hz, _ = res
                self._bode_plot.set_cutoff_fc(fc_hz)
            else:
                self._bode_plot.set_cutoff_fc(None)
        else:
            self._bode_plot.set_cutoff_fc(None)

    def _on_y_axis_changed(self):
        if self._bode_plot and self._points:
            self._bode_plot.set_bode_points(self._points, y_linear=self._y_linear.isChecked())
            self._on_display_changed()

    def _on_adjust_view(self):
        if self._bode_plot:
            self._bode_plot.auto_range()

    def _on_export(self):
        if not self._bode_plot:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter graphique Bode", "", "PNG (*.png);;Tous (*)"
        )
        if not path:
            return
        if self._bode_plot.export_image(path):
            QMessageBox.information(self, "Export", f"Graphique enregistré : {path}")
        else:
            QMessageBox.warning(self, "Export", "Échec de l'export de l'image.")
