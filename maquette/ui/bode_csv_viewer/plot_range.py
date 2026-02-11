"""
Gestion des plages de vue du graphique Bode (axe X en log10(Hz), axe Y linéaire).
Conversion Hz ↔ log10(Hz) pour pyqtgraph ViewBox. Module autonome.
"""
import math
from typing import Optional, Tuple, Any

from core.app_logger import get_logger

logger = get_logger(__name__)

AUTO_RANGE_MARGIN = 0.05
"""Marge relative pour l'auto-range (évite que la courbe colle aux bords)."""


def compute_data_range(
    freqs: list,
    y_values: list,
    margin: float = AUTO_RANGE_MARGIN,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Retourne (x_min, x_max, y_min, y_max) avec marge, ou None si données vides.
    freqs: fréquences en Hz ; y_values: gain (dB ou Us/Ue).
    """
    if not freqs or not y_values or len(freqs) != len(y_values):
        return None
    x_min, x_max = min(freqs), max(freqs)
    y_min, y_max = min(y_values), max(y_values)
    dx = (x_max - x_min) * margin or x_min * 0.1
    dy = (y_max - y_min) * margin or 1.0
    return (
        max(x_min - dx, 0.1) if x_min > 0 else 0.1,
        x_max + dx,
        y_min - dy,
        y_max + dy,
    )


def apply_view_range(
    vb: Any,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    log_mode_x: bool = True,
) -> None:
    """
    Applique les limites (fréquence en Hz, gain) à la ViewBox.
    En mode log (axe X), convertit Hz → log10(Hz) pour pyqtgraph.
    """
    vb.disableAutoRange()
    if log_mode_x:
        x_lo = math.log10(max(float(x_min), 1e-307))
        x_hi = math.log10(min(float(x_max), 1e308))
    else:
        x_lo, x_hi = float(x_min), float(x_max)
    vb.setRange(
        xRange=(x_lo, x_hi),
        yRange=(float(y_min), float(y_max)),
        padding=0,
        update=True,
        disableAutoRange=True,
    )
    logger.debug(
        "Bode plot_range apply_view_range: x=%.6g..%.6g Hz, y=%.6g..%.6g",
        x_min, x_max, y_min, y_max,
    )


def read_view_range(
    vb: Any,
    log_mode_x: bool = True,
    fallback: Optional[Tuple[float, float, float, float]] = None,
) -> Tuple[float, float, float, float]:
    """
    Lit (x_min, x_max, y_min, y_max) en Hz / gain depuis la ViewBox.
    Si axe X en log, interprète viewRange X comme log10(Hz) et convertit en Hz.
    Si plage par défaut (ex. 1e-200..1e200) et fallback fourni, retourne fallback.
    """
    r = vb.viewRange()
    x_lo, x_hi = r[0][0], r[0][1]
    y_lo, y_hi = r[1][0], r[1][1]
    if log_mode_x:
        exp_lo = max(-307.6, min(308.2, x_lo))
        exp_hi = max(-307.6, min(308.2, x_hi))
        x_lo = 10.0 ** exp_lo
        x_hi = 10.0 ** exp_hi
        if not math.isfinite(x_lo):
            x_lo = 1e-307
        if not math.isfinite(x_hi):
            x_hi = 1e308
        if fallback is not None and (x_hi > 1e200 or x_lo < 1e-200):
            return fallback
    return (x_lo, x_hi, y_lo, y_hi)
