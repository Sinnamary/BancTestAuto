"""
Fenêtre de visualisation Bode CSV. Totalement indépendante du banc de test et des autres dialogs.
"""
from pathlib import Path
from typing import Optional

from core.app_logger import get_logger

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
from .cutoff import Cutoff3DbFinder
from .smoothing import has_savgol

logger = get_logger(__name__)


def _fmt_freq(hz: float) -> str:
    """Ex. 1234.5 -> '1,23 kHz'."""
    if hz >= 1000:
        return f"{hz / 1000:.2f} kHz"
    return f"{hz:.1f} Hz"


class BodeCsvViewerDialog(QDialog):
    """Dialogue autonome : charge et affiche un CSV Bode avec ses propres contrôles."""
    def __init__(
        self,
        parent=None,
        csv_path: str = "",
        dataset: Optional[BodeCsvDataset] = None,
        config: Optional[dict] = None,
    ):
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
        # Fond noir par défaut (l'utilisateur peut choisir Blanc dans Affichage)
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
        self._background_combo.setCurrentIndex(0 if self._options.plot_background_dark else 1)
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
        self._grid_minor_cb = QCheckBox("Quadrillage mineur")
        self._grid_minor_cb.setToolTip("Lignes intermédiaires pour lecture fine")
        self._grid_minor_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._grid_minor_cb)
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
        disp_layout.addWidget(QLabel("Algo:"))
        self._smooth_method_combo = QComboBox()
        for label, use_savgol in BodeViewOptions.SMOOTH_METHODS:
            if use_savgol and not has_savgol():
                continue
            self._smooth_method_combo.addItem(label, use_savgol)
        self._smooth_method_combo.currentIndexChanged.connect(self._apply_options)
        disp_layout.addWidget(self._smooth_method_combo)
        self._raw_cb = QCheckBox("Courbe brute + lissée")
        self._raw_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._raw_cb)
        self._peaks_cb = QCheckBox("Pics/creux")
        self._peaks_cb.setToolTip("Marqueurs sur les maxima et minima locaux")
        self._peaks_cb.toggled.connect(self._apply_options)
        disp_layout.addWidget(self._peaks_cb)
        disp_layout.addStretch()
        layout.addWidget(disp_gb)

        search_gb = QGroupBox("Recherche gain cible")
        search_layout = QHBoxLayout(search_gb)
        search_layout.addWidget(QLabel("Gain (dB):"))
        self._target_gain_spin = QDoubleSpinBox()
        self._target_gain_spin.setRange(-100, 50)
        self._target_gain_spin.setDecimals(1)
        self._target_gain_spin.setValue(-3)
        self._target_gain_spin.setSingleStep(1)
        self._target_gain_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        search_layout.addWidget(self._target_gain_spin)
        self._search_target_btn = QPushButton("Rechercher")
        self._search_target_btn.setToolTip("Affiche les fréquences où la courbe coupe ce gain")
        self._search_target_btn.clicked.connect(self._on_search_target_gain)
        search_layout.addWidget(self._search_target_btn)
        self._clear_target_btn = QPushButton("Effacer la ligne")
        self._clear_target_btn.setToolTip("Supprime la ligne de gain cible et les marqueurs de fréquence")
        self._clear_target_btn.clicked.connect(self._on_clear_target_gain)
        search_layout.addWidget(self._clear_target_btn)
        self._target_result_label = QLabel("")
        self._target_result_label.setStyleSheet("color: gray; font-size: 10px;")
        search_layout.addWidget(self._target_result_label)
        search_layout.addStretch()
        layout.addWidget(search_gb)

        scale_gb = QGroupBox("Échelles / Zoom")
        scale_layout = QHBoxLayout(scale_gb)
        scale_layout.addWidget(QLabel("F min (Hz):"))
        self._f_min_spin = QDoubleSpinBox()
        self._f_min_spin.setRange(0.1, 1e9)
        self._f_min_spin.setDecimals(2)
        self._f_min_spin.setValue(10)
        self._f_min_spin.setSingleStep(10)
        self._f_min_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        scale_layout.addWidget(self._f_min_spin)
        scale_layout.addWidget(QLabel("F max (Hz):"))
        self._f_max_spin = QDoubleSpinBox()
        self._f_max_spin.setRange(0.1, 1e9)
        self._f_max_spin.setDecimals(2)
        self._f_max_spin.setValue(100000)
        self._f_max_spin.setSingleStep(1000)
        self._f_max_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        scale_layout.addWidget(self._f_max_spin)
        scale_layout.addWidget(QLabel("Gain min:"))
        self._gain_min_spin = QDoubleSpinBox()
        self._gain_min_spin.setRange(-300, 100)
        self._gain_min_spin.setDecimals(2)
        self._gain_min_spin.setValue(-50)
        self._gain_min_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        scale_layout.addWidget(self._gain_min_spin)
        scale_layout.addWidget(QLabel("Gain max:"))
        self._gain_max_spin = QDoubleSpinBox()
        self._gain_max_spin.setRange(-300, 100)
        self._gain_max_spin.setDecimals(2)
        self._gain_max_spin.setValue(5)
        self._gain_max_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
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

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: gray; font-size: 11px;")
        self._info_label.setToolTip("Résumé des données pour l'étude de la courbe")
        layout.addWidget(self._info_label)

        btn_layout = QHBoxLayout()
        self._adjust_btn = QPushButton("Ajuster vue")
        self._adjust_btn.setToolTip("Recadrer la vue sur toutes les données")
        self._adjust_btn.clicked.connect(self._on_adjust_view)
        btn_layout.addWidget(self._adjust_btn)
        btn_layout.addStretch()
        self._export_btn = QPushButton("Exporter en PNG")
        self._export_btn.clicked.connect(self._on_export)
        btn_layout.addWidget(self._export_btn)
        self._export_csv_btn = QPushButton("Exporter les points CSV")
        self._export_csv_btn.setToolTip("Enregistre f_Hz, Us_V, Us_Ue, Gain_dB")
        self._export_csv_btn.clicked.connect(self._on_export_csv)
        btn_layout.addWidget(self._export_csv_btn)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._y_linear.toggled.connect(self._on_y_changed)
        self._y_db.toggled.connect(self._on_y_changed)
        self._plot.set_dataset(self._dataset)
        self._apply_options()
        self._sync_scale_spins_from_view()
        self._update_info_panel()

    def _load_csv(self, path: str) -> None:
        loader = BodeCsvFileLoader()
        self._dataset = loader.load(path)

    def _on_y_changed(self) -> None:
        self._options.y_linear = self._y_linear.isChecked()
        self._plot.set_y_linear(self._options.y_linear)
        self._apply_options()

    def _apply_options(self) -> None:
        self._options.grid_visible = self._grid_cb.isChecked()
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
        use_savgol = (
            self._smooth_method_combo.currentData() is True
            if self._smooth_method_combo.currentData() is not None
            else False
        )
        self._plot.set_smoothing(
            self._options.smooth_window,
            self._options.show_raw_curve,
            use_savgol=use_savgol,
        )
        self._plot.set_y_linear(self._options.y_linear)
        self._plot.set_peaks_visible(self._peaks_cb.isChecked())
        self._plot.set_minor_grid_visible(self._grid_minor_cb.isChecked())
        self._update_info_panel()

    def _update_info_panel(self) -> None:
        """Affiche fc (-3 dB), gain max et nombre de points pour l'étude de la courbe."""
        if not self._dataset or self._dataset.is_empty():
            self._info_label.setText("")
            return
        n = self._dataset.count
        gains_db = self._dataset.gains_db()
        g_max = max(gains_db) if gains_db else 0.0
        finder = Cutoff3DbFinder()
        cutoffs = finder.find_all(self._dataset)
        if cutoffs:
            fc_str = "  |  ".join(
                f"fc{' ' + str(k + 1) if len(cutoffs) > 1 else ''} = {_fmt_freq(r.fc_hz)}"
                for k, r in enumerate(cutoffs)
            )
        else:
            fc_str = "fc — (pas de coupure -3 dB)"
        self._info_label.setText(f"  {fc_str}  |  G_max = {g_max:.2f} dB  |  N = {n} points")

    def _on_adjust_view(self) -> None:
        self._plot.auto_range()
        self._sync_scale_spins_from_view()

    def _sync_scale_spins_from_view(self) -> None:
        """Met à jour les spinboxes avec la plage actuelle de la vue."""
        try:
            x_min, x_max, y_min, y_max = self._plot.get_view_range()
            logger.debug(
                "Bode dialog _sync_scale_spins_from_view: F min/max=%.6g / %.6g Hz, Gain min/max=%.6g / %.6g → spinboxes",
                x_min, x_max, y_min, y_max,
            )
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
        logger.debug(
            "Bode dialog Appliquer les limites: F min=%.6g, F max=%.6g Hz, Gain min=%.6g, Gain max=%.6g",
            f_min, f_max, gain_min, gain_max,
        )
        self._plot.set_view_range(f_min, f_max, gain_min, gain_max)

    def _on_zoom_zone_toggled(self, checked: bool) -> None:
        self._plot.set_rect_zoom_mode(checked)

    def _on_search_target_gain(self) -> None:
        if not self._dataset or self._dataset.is_empty():
            self._target_result_label.setText("(aucune donnée)")
            return
        target_db = self._target_gain_spin.value()
        finder = Cutoff3DbFinder()
        results = finder.find_crossings_at_gain(self._dataset, target_db)
        self._plot.set_target_gain_search(target_db, [r.fc_hz for r in results])
        if results:
            self._target_result_label.setText(
                "  |  ".join(f"f = {_fmt_freq(r.fc_hz)}" for r in results)
            )
        else:
            self._target_result_label.setText("(aucune intersection)")

    def _on_clear_target_gain(self) -> None:
        """Supprime la ligne de gain cible et les marqueurs de fréquence du graphique."""
        self._plot.set_target_gain_search(None)
        self._target_result_label.setText("")

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

    def _on_export_csv(self) -> None:
        if not self._dataset or self._dataset.is_empty():
            QMessageBox.warning(self, "Export", "Aucune donnée à exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les points", "", "CSV (*.csv);;Tous (*)"
        )
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["f_Hz", "Us_V", "Us_Ue", "Gain_dB"])
                for p in self._dataset.points:
                    w.writerow([p.f_hz, p.us_v, p.gain_linear, p.gain_db])
            QMessageBox.information(self, "Export", f"Points enregistrés : {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export", f"Échec : {e}")


def open_viewer(parent=None, csv_path: str = "") -> None:
    """Point d'entrée unique : ouvre le dialogue viewer avec le fichier CSV (chargé par le viewer)."""
    dlg = BodeCsvViewerDialog(parent, csv_path=csv_path)
    dlg.exec()
