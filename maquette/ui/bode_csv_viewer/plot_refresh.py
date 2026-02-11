"""
Logique de rafraîchissement des courbes du widget Bode (gain, phase, cutoff, peaks).
Extrait de plot_widget pour réduire la complexité cyclomatique du widget.
"""
from typing import Any

from core.app_logger import get_logger

logger = get_logger(__name__)


def refresh_bode_plot(widget: Any) -> None:
    """
    Met à jour les courbes, la phase, les marqueurs cutoff et peaks selon l'état du widget.
    Le widget doit exposer : _dataset, _y_linear, _smooth_window, _show_raw, _smooth_savgol,
    _show_gain, _show_phase, _curves, _phase_overlay, _cutoff_viz, _peaks_overlay.
    """
    if not widget._dataset or widget._dataset.is_empty():
        logger.debug("Bode plot _refresh: dataset vide → courbes vidées")
        widget._curves.clear()
        widget._phase_overlay.clear_phase_data()
        widget._cutoff_viz.set_level(None)
        widget._cutoff_viz.set_cutoff_frequencies([])
        widget._peaks_overlay.update(None, widget._y_linear)
        return
    widget._curves.set_curve_visible(widget._show_gain)
    widget._curves.set_data(
        widget._dataset,
        y_linear=widget._y_linear,
        smooth_window=widget._smooth_window,
        show_raw=widget._show_raw,
        smooth_savgol_flag=widget._smooth_savgol,
    )
    has_phase = widget._dataset.has_phase()
    if has_phase:
        freqs = widget._dataset.freqs_hz()
        phases = widget._dataset.phases_deg()
        ys_phase = [(p if p is not None else 0.0) for p in phases]
        logger.debug(
            "Bode plot _refresh PHASE: freqs [%.6g, %.6g] (%d pts) | phase ° [%.6g, %.6g]",
            min(freqs), max(freqs), len(freqs), min(ys_phase), max(ys_phase),
        )
        widget._phase_overlay.set_visible(widget._show_phase)
        widget._phase_overlay.set_phase_data(freqs, ys_phase)
    else:
        widget._phase_overlay.clear_phase_data()
    widget._cutoff_viz.set_level(None)
    widget._cutoff_viz.set_cutoff_frequencies([])
    widget._peaks_overlay.update(widget._dataset, widget._y_linear)
    widget._cutoff_viz.update_label_position()
    logger.debug("Bode plot _refresh: sortie")
