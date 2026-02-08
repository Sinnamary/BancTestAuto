"""
Fenêtre de visualisation Bode CSV. Totalement indépendante du banc de test et des autres dialogs.
"""
from pathlib import Path
from typing import Optional

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
    QDoubleSpinBox,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from .model import BodeCsvDataset
from .csv_loader import BodeCsvFileLoader
from .plot_widget import BodeCsvPlotWidget
from .view_state import BodeViewOptions


class BodeCsvViewerDialog(QDialog):
    """Dialogue autonome : charge et affiche un CSV Bode avec ses propres contrôles."""
    def __init__(self, parent=None, csv_path: str = "", dataset: Optional[BodeCsvDataset] = None):
        super().__init__(parent)
        self.setWindowTitle("Graphique Bode — Banc filtre")
        if csv_path:
            self.setWindowTitle(f"Graphique Bode — {Path(csv_path).name}")
        self.setMinimumSize(640, 480)
        self.resize(800, 500)
        self._csv_path = csv_path
        self._dataset: BodeCsvDataset = dataset if dataset is not None else BodeCsvDataset([])
        if csv_path and dataset is None:
            self._load_csv(csv_path)
        self._options = BodeViewOptions.default()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        y_gb = QGroupBox("Ordonnée (Y)")
        y_layout = QHBoxLayout(y_gb)
        self._y_group = QButtonGroup(self)
        self._y_linear = QRadioButton("Gain linéaire (Us/Ue)")
        self._y_db = QRadioButton("Gain en dB")
        self._y_db.setChecked(True)
        self._y_group.addButton(self._y_linear)
        self._y_group.addButton(self._y_db)
        y_layout.addWidget(self._y_linear)
        y_layout.addWidget(self._y_db)
        y_layout.addStretch()
        layout.addWidget(y_gb)

        disp_gb = QGroupBox("Affichage")
        disp_layout = QHBoxLayout(disp_gb)
        disp_layout.addWidget(QLabel("Fond:"))
        self._background_combo = QComboBox()
        for label, dark in BodeViewOptions.BACKGROUND_CHOICES:
            self._background_combo.addItem(label, dark)
        self._background_combo.setCurrentIndex(0)
        self._background_combo.currentIndexChanged.connect(self._apply_options)
        disp_layout.addWidget(self._background_combo)
        disp_layout.addWidget(QLabel("Couleur courbe:"))
        self._curve_color_combo = QComboBox()
        for label, hex_color in BodeViewOptions.CURVE_COLOR_CHOICES:
            self._curve_color_combo.addItem(label, hex_color)
        self._curve_color_combo.currentIndexChanged.connect(self._apply_options)
        disp_layout.addWidget(self._curve_color_combo)
        self._grid_cb = QCheckBox("Quadrillage")
        self._grid_cb.setChecked(True)
        self._grid_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._grid_cb)
        self._smooth_cb = QCheckBox("Lissage")
        self._smooth_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._smooth_cb)
        disp_layout.addWidget(QLabel("Fenêtre:"))
        self._smooth_combo = QComboBox()
        for w in BodeViewOptions.SMOOTH_WINDOW_CHOICES:
            self._smooth_combo.addItem(str(w), w)
        self._smooth_combo.setCurrentIndex(1)
        self._smooth_combo.currentIndexChanged.connect(self._apply_options)
        disp_layout.addWidget(self._smooth_combo)
        self._raw_cb = QCheckBox("Courbe brute + lissée")
        self._raw_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._raw_cb)
        self._cutoff_cb = QCheckBox("Ligne à -3 dB")
        self._cutoff_cb.setToolTip("Affiche une ligne horizontale rouge au niveau -3 dB (référence coupure)")
        self._cutoff_cb.setChecked(True)
        self._cutoff_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._cutoff_cb)
        disp_layout.addStretch()
        layout.addWidget(disp_gb)

        scale_gb = QGroupBox("Échelles / Zoom")
        scale_layout = QHBoxLayout(scale_gb)
        scale_layout.addWidget(QLabel("F min (Hz):"))
        self._f_min_spin = QDoubleSpinBox()
        self._f_min_spin.setRange(0.1, 1e9)
        self._f_min_spin.setDecimals(2)
        self._f_min_spin.setValue(10)
        self._f_min_spin.setSingleStep(10)
        scale_layout.addWidget(self._f_min_spin)
        scale_layout.addWidget(QLabel("F max (Hz):"))
        self._f_max_spin = QDoubleSpinBox()
        self._f_max_spin.setRange(0.1, 1e9)
        self._f_max_spin.setDecimals(2)
        self._f_max_spin.setValue(100000)
        self._f_max_spin.setSingleStep(1000)
        scale_layout.addWidget(self._f_max_spin)
        scale_layout.addWidget(QLabel("Gain min:"))
        self._gain_min_spin = QDoubleSpinBox()
        self._gain_min_spin.setRange(-300, 100)
        self._gain_min_spin.setDecimals(2)
        self._gain_min_spin.setValue(-50)
        scale_layout.addWidget(self._gain_min_spin)
        scale_layout.addWidget(QLabel("Gain max:"))
        self._gain_max_spin = QDoubleSpinBox()
        self._gain_max_spin.setRange(-300, 100)
        self._gain_max_spin.setDecimals(2)
        self._gain_max_spin.setValue(5)
        scale_layout.addWidget(self._gain_max_spin)
        self._apply_scale_btn = QPushButton("Appliquer les limites")
        self._apply_scale_btn.setToolTip("Appliquer les valeurs ci-dessus aux axes du graphique")
        self._apply_scale_btn.clicked.connect(self._on_apply_scale)
        scale_layout.addWidget(self._apply_scale_btn)
        self._zoom_zone_cb = QCheckBox("Zoom sur zone (glisser)")
        self._zoom_zone_cb.setToolTip("Coché : glisser sur le graphique pour sélectionner une zone et zoomer. Décoché : glisser = déplacer la vue. Molette = zoom toujours actif.")
        self._zoom_zone_cb.toggled.connect(self._on_zoom_zone_toggled)
        scale_layout.addWidget(self._zoom_zone_cb)
        scale_layout.addStretch()
        layout.addWidget(scale_gb)

        self._plot = BodeCsvPlotWidget()
        self._plot.setMinimumHeight(280)
        layout.addWidget(self._plot)

        btn_layout = QHBoxLayout()
        self._adjust_btn = QPushButton("Ajuster vue")
        self._adjust_btn.setToolTip("Recadrer la vue sur toutes les données")
        self._adjust_btn.clicked.connect(self._on_adjust_view)
        btn_layout.addWidget(self._adjust_btn)
        btn_layout.addStretch()
        self._export_btn = QPushButton("Exporter en PNG")
        self._export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self._export_btn)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._y_linear.toggled.connect(self._on_y_changed)
        self._y_db.toggled.connect(self._on_y_changed)
        self._plot.set_dataset(self._dataset)
        self._apply_options()
        self._sync_scale_spins_from_view()

    def _load_csv(self, path: str) -> None:
        loader = BodeCsvFileLoader()
        self._dataset = loader.load(path)

    def _on_y_changed(self) -> None:
        self._options.y_linear = self._y_linear.isChecked()
        self._plot.set_y_linear(self._options.y_linear)
        self._apply_options()

    def _apply_options(self) -> None:
        self._options.grid_visible = self._grid_cb.isChecked()
        self._options.show_cutoff = self._cutoff_cb.isChecked()
        window = self._smooth_combo.currentData() if self._smooth_cb.isChecked() else 0
        if window is None:
            window = 5
        self._options.smooth_window = window
        self._options.show_raw_curve = self._raw_cb.isChecked()
        dark = self._background_combo.currentData()
        if dark is not None:
            self._options.plot_background_dark = dark
            self._plot.set_background_dark(dark)
        color = self._curve_color_combo.currentData()
        if color is not None:
            self._options.curve_color = color
            self._plot.set_curve_color(color)
        self._plot.set_grid_visible(self._options.grid_visible)
        self._plot.set_smoothing(self._options.smooth_window, self._options.show_raw_curve)
        self._plot.set_cutoff_visible(self._options.show_cutoff)
        self._plot.set_y_linear(self._options.y_linear)

    def _on_adjust_view(self) -> None:
        self._plot.auto_range()
        self._sync_scale_spins_from_view()

    def _sync_scale_spins_from_view(self) -> None:
        """Met à jour les spinboxes avec la plage actuelle de la vue."""
        try:
            x_min, x_max, y_min, y_max = self._plot.get_view_range()
            self._f_min_spin.setValue(x_min)
            self._f_max_spin.setValue(x_max)
            self._gain_min_spin.setValue(y_min)
            self._gain_max_spin.setValue(y_max)
        except Exception:
            pass

    def _on_apply_scale(self) -> None:
        f_min = self._f_min_spin.value()
        f_max = self._f_max_spin.value()
        if f_min >= f_max:
            f_max = f_min + 1
            self._f_max_spin.setValue(f_max)
        gain_min = self._gain_min_spin.value()
        gain_max = self._gain_max_spin.value()
        if gain_min >= gain_max:
            gain_max = gain_min + 1
            self._gain_max_spin.setValue(gain_max)
        self._plot.set_view_range(f_min, f_max, gain_min, gain_max)

    def _on_zoom_zone_toggled(self, checked: bool) -> None:
        self._plot.set_rect_zoom_mode(checked)

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter graphique Bode", "", "PNG (*.png);;Tous (*)"
        )
        if not path:
            return
        if self._plot.export_png(path):
            QMessageBox.information(self, "Export", f"Graphique enregistré : {path}")
        else:
            QMessageBox.warning(self, "Export", "Échec de l'export.")


def open_viewer(parent=None, csv_path: str = "") -> None:
    """Point d'entrée unique : ouvre le dialogue viewer avec le fichier CSV (chargé par le viewer)."""
    dlg = BodeCsvViewerDialog(parent, csv_path=csv_path)
    dlg.exec()
