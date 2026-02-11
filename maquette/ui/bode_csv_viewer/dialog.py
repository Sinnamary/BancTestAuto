"""
Fenêtre de visualisation Bode CSV. Totalement indépendante du banc de test et des autres dialogs.
Lit/écrit la section config["bode_viewer"] pour persister les options (sauvegarde via Fichier → Sauvegarder config).
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.app_logger import get_logger

try:
    from config.settings import get_bode_viewer_config
except ImportError:
    def get_bode_viewer_config(c: dict) -> dict:
        return (c.get("bode_viewer") or {}).copy()

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFileDialog,
    QMessageBox,
)

from .model import BodeCsvDataset
from .csv_loader import BodeCsvFileLoader
from .plot_widget import BodeCsvPlotWidget
from .view_state import BodeViewOptions
from .cutoff import Cutoff3DbFinder
from .smoothing import has_savgol
from .formatters import format_freq_hz
from .panel_y_axis import build_y_axis_panel
from .panel_display import build_display_panel
from .panel_search import build_search_panel
from .panel_scale import build_scale_panel
from .panel_buttons import build_buttons_layout

logger = get_logger(__name__)


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
        self._config: Optional[dict] = config  # config mutable : on y écrit bode_viewer à la fermeture
        self._dataset: BodeCsvDataset = dataset if dataset is not None else BodeCsvDataset([])
        if csv_path and dataset is None:
            self._load_csv(csv_path)
        self._options = BodeViewOptions.default()
        self._build_ui()
        # Appliquer la config bode_viewer si fournie (sauvegardée via Fichier → Sauvegarder config)
        if self._config:
            self._apply_bode_viewer_config(get_bode_viewer_config(self._config))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addWidget(build_y_axis_panel(self))
        layout.addWidget(build_display_panel(self, self._apply_options))
        layout.addWidget(build_search_panel(self, self._on_search_target_gain, self._on_clear_target_gain))
        layout.addWidget(build_scale_panel(self, self._on_apply_scale, self._on_zoom_zone_toggled))

        self._plot = BodeCsvPlotWidget()
        self._plot.setMinimumHeight(300)
        layout.addWidget(self._plot)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet(
            "color: #606060; font-size: 11px; font-weight: 500; padding: 4px 0;"
        )
        self._info_label.setToolTip("Résumé des données pour l'étude de la courbe")
        layout.addWidget(self._info_label)

        layout.addLayout(build_buttons_layout(self, self._on_adjust_view, self._on_export, self._on_export_csv))

        self._y_linear.toggled.connect(self._on_y_changed)
        self._y_db.toggled.connect(self._on_y_changed)
        self._plot.set_dataset(self._dataset)
        has_phase = self._dataset.has_phase()
        self._show_gain_cb.setVisible(has_phase)
        self._show_phase_cb.setVisible(has_phase)
        if has_phase:
            self._plot.set_show_gain(self._show_gain_cb.isChecked())
            self._plot.set_show_phase(self._show_phase_cb.isChecked())
        self._apply_options()
        self._sync_scale_spins_from_view()
        self._update_info_panel()

    def _apply_bode_viewer_config(self, d: dict[str, Any]) -> None:
        """Applique la section bode_viewer de la config aux widgets (chargement)."""
        if not d:
            return
        self._background_combo.setCurrentIndex(0 if d.get("plot_background_dark", True) else 1)
        color = d.get("curve_color", "#e0c040")
        for i in range(self._curve_color_combo.count()):
            if self._curve_color_combo.itemData(i) == color:
                self._curve_color_combo.setCurrentIndex(i)
                break
        self._grid_cb.setChecked(d.get("grid_visible", True))
        self._grid_minor_cb.setChecked(d.get("grid_minor_visible", False))
        sw = int(d.get("smooth_window", 0))
        self._smooth_cb.setChecked(sw > 0)
        for i in range(self._smooth_combo.count()):
            if self._smooth_combo.itemData(i) == sw:
                self._smooth_combo.setCurrentIndex(i)
                break
        else:
            if self._smooth_combo.count():
                self._smooth_combo.setCurrentIndex(min(1, self._smooth_combo.count() - 1))
        use_savgol = d.get("smooth_savgol", False)
        for i in range(self._smooth_method_combo.count()):
            if self._smooth_method_combo.itemData(i) is use_savgol:
                self._smooth_method_combo.setCurrentIndex(i)
                break
        self._raw_cb.setChecked(d.get("show_raw_curve", False))
        self._peaks_cb.setChecked(d.get("peaks_visible", False))
        y_lin = bool(d.get("y_linear", False))
        self._y_linear.setChecked(y_lin)
        self._y_db.setChecked(not y_lin)
        self._apply_options()

    def _get_bode_viewer_state(self) -> dict[str, Any]:
        """Retourne l'état actuel des options (pour sauvegarde dans config)."""
        use_savgol = self._smooth_method_combo.currentData() is True
        return {
            "plot_background_dark": self._background_combo.currentData() is True,
            "curve_color": self._curve_color_combo.currentData() or "#e0c040",
            "grid_visible": self._grid_cb.isChecked(),
            "grid_minor_visible": self._grid_minor_cb.isChecked(),
            "smooth_window": self._smooth_combo.currentData() if self._smooth_cb.isChecked() else 0,
            "show_raw_curve": self._raw_cb.isChecked(),
            "smooth_savgol": use_savgol,
            "y_linear": self._y_linear.isChecked(),
            "peaks_visible": self._peaks_cb.isChecked(),
        }

    def _save_bode_viewer_to_config(self) -> None:
        """Écrit les options actuelles dans config[\"bode_viewer\"] (persistées par Fichier → Sauvegarder config)."""
        if self._config is not None:
            self._config["bode_viewer"] = self._get_bode_viewer_state()

    def accept(self) -> None:
        self._save_bode_viewer_to_config()
        super().accept()

    def reject(self) -> None:
        self._save_bode_viewer_to_config()
        super().reject()

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
        if self._dataset.has_phase():
            self._plot.set_show_gain(self._show_gain_cb.isChecked())
            self._plot.set_show_phase(self._show_phase_cb.isChecked())
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
                f"fc{' ' + str(k + 1) if len(cutoffs) > 1 else ''} = {format_freq_hz(r.fc_hz)}"
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
                "  |  ".join(f"f = {format_freq_hz(r.fc_hz)}" for r in results)
            )
        else:
            self._target_result_label.setText("(aucune intersection)")

    def _on_clear_target_gain(self) -> None:
        """Supprime la ligne de gain cible et les marqueurs de fréquence du graphique."""
        self._plot.set_target_gain_search(None)
        self._target_result_label.setText("")

    def _on_export(self) -> None:
        default_dir = Path("datas/png") if Path("datas/png").exists() else Path(".")
        default_name = f"bode_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        default_path = str(default_dir / default_name)
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter graphique Bode", default_path, "PNG (*.png);;Tous (*)"
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
        default_dir = Path("datas/csv") if Path("datas/csv").exists() else Path(".")
        default_name = f"bode_points_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        default_path = str(default_dir / default_name)
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les points", default_path, "CSV (*.csv);;Tous (*)"
        )
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, delimiter=";")
                if self._dataset.has_phase():
                    w.writerow(["f_Hz", "Us_V", "Us_Ue", "Gain_dB", "Ue_V", "Phase_deg"])
                    for p in self._dataset.points:
                        ue_v = getattr(p, "ue_v", None)
                        phase_deg = getattr(p, "phase_deg", None)
                        w.writerow([p.f_hz, p.us_v, p.gain_linear, p.gain_db, ue_v if ue_v is not None else "", phase_deg if phase_deg is not None else ""])
                else:
                    w.writerow(["f_Hz", "Us_V", "Us_Ue", "Gain_dB"])
                    for p in self._dataset.points:
                        w.writerow([p.f_hz, p.us_v, p.gain_linear, p.gain_db])
            QMessageBox.information(self, "Export", f"Points enregistrés : {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export", f"Échec : {e}")
