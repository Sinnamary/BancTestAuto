"""
Actions et logique du dialogue Bode CSV : chargement, config, état, formatage info.
Permet d'alléger dialog.py en déplaçant la logique métier ici.
"""
from typing import Any

from .model import BodeCsvDataset
from .csv_loader import BodeCsvFileLoader
from .cutoff import Cutoff3DbFinder
from .formatters import format_freq_hz


def load_csv(path: str) -> BodeCsvDataset:
    """Charge un fichier CSV Bode et retourne le dataset."""
    loader = BodeCsvFileLoader()
    return loader.load(path)


def apply_bode_viewer_config_to_dialog(dialog: Any, d: dict[str, Any]) -> None:
    """Applique la section bode_viewer de la config aux widgets du dialogue (chargement)."""
    if not d:
        return
    dialog._background_combo.setCurrentIndex(0 if d.get("plot_background_dark", True) else 1)
    color = d.get("curve_color", "#e0c040")
    for i in range(dialog._curve_color_combo.count()):
        if dialog._curve_color_combo.itemData(i) == color:
            dialog._curve_color_combo.setCurrentIndex(i)
            break
    dialog._grid_cb.setChecked(d.get("grid_visible", True))
    dialog._grid_minor_cb.setChecked(d.get("grid_minor_visible", False))
    sw = int(d.get("smooth_window", 0))
    dialog._smooth_cb.setChecked(sw > 0)
    for i in range(dialog._smooth_combo.count()):
        if dialog._smooth_combo.itemData(i) == sw:
            dialog._smooth_combo.setCurrentIndex(i)
            break
    else:
        if dialog._smooth_combo.count():
            dialog._smooth_combo.setCurrentIndex(min(1, dialog._smooth_combo.count() - 1))
    use_savgol = d.get("smooth_savgol", False)
    for i in range(dialog._smooth_method_combo.count()):
        if dialog._smooth_method_combo.itemData(i) is use_savgol:
            dialog._smooth_method_combo.setCurrentIndex(i)
            break
    dialog._raw_cb.setChecked(d.get("show_raw_curve", False))
    dialog._peaks_cb.setChecked(d.get("peaks_visible", False))
    y_lin = bool(d.get("y_linear", False))
    dialog._y_linear.setChecked(y_lin)
    dialog._y_db.setChecked(not y_lin)
    dialog._apply_options()


def get_bode_viewer_state_from_dialog(dialog: Any) -> dict[str, Any]:
    """Retourne l'état actuel des options du dialogue (pour sauvegarde dans config)."""
    use_savgol = dialog._smooth_method_combo.currentData() is True
    return {
        "plot_background_dark": dialog._background_combo.currentData() is True,
        "curve_color": dialog._curve_color_combo.currentData() or "#e0c040",
        "grid_visible": dialog._grid_cb.isChecked(),
        "grid_minor_visible": dialog._grid_minor_cb.isChecked(),
        "smooth_window": dialog._smooth_combo.currentData() if dialog._smooth_cb.isChecked() else 0,
        "show_raw_curve": dialog._raw_cb.isChecked(),
        "smooth_savgol": use_savgol,
        "y_linear": dialog._y_linear.isChecked(),
        "peaks_visible": dialog._peaks_cb.isChecked(),
    }


def format_info_panel_text(dataset: BodeCsvDataset) -> str:
    """Génère le texte du panneau d'info (fc -3 dB, G_max, N points). Retourne '' si dataset vide."""
    if not dataset or dataset.is_empty():
        return ""
    n = dataset.count
    gains_db = dataset.gains_db()
    g_max = max(gains_db) if gains_db else 0.0
    finder = Cutoff3DbFinder()
    cutoffs = finder.find_all(dataset)
    if cutoffs:
        fc_str = "  |  ".join(
            f"fc{' ' + str(k + 1) if len(cutoffs) > 1 else ''} = {format_freq_hz(r.fc_hz)}"
            for k, r in enumerate(cutoffs)
        )
    else:
        fc_str = "fc — (pas de coupure -3 dB)"
    return f"  {fc_str}  |  G_max = {g_max:.2f} dB  |  N = {n} points"
