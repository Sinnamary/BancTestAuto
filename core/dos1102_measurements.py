"""
Helpers pour les mesures DOS1102 : formatage des résultats, calcul de phase.
Réutilisable sans UI (ex. banc filtre Bode phase, scripts).
"""
from . import dos1102_commands as CMD


def format_measurements_text(measurements: dict[str, str], add_bode_hint: bool = False) -> str:
    """
    Formate un dictionnaire { libellé: valeur } en texte une ligne par mesure.
    Si add_bode_hint, ajoute une ligne rappelant la formule Bode phase.
    """
    lines = [f"{k}: {v}" for k, v in measurements.items()]
    if add_bode_hint:
        lines.append("")
        lines.append("Pour Bode phase : φ (°) = (délai / période) × 360 (période sur CH1 ou CH2)")
    return "\n".join(lines)


def phase_deg_from_delay(delay_s: float, period_s: float) -> float | None:
    """
    Calcule la différence de phase en degrés à partir du délai et de la période.
    Retourne None si période <= 0 ou valeurs invalides.
    """
    try:
        if period_s is None or period_s <= 0:
            return None
        d = float(delay_s)
        p = float(period_s)
        if p <= 0:
            return None
        return (d / p) * 360.0
    except (TypeError, ValueError):
        return None


def get_measure_types_per_channel():
    """Retourne la liste (libellé, type SCPI) des mesures par voie."""
    return list(CMD.MEAS_TYPES_PER_CHANNEL)


def get_measure_types_inter_channel():
    """Retourne la liste (libellé, type SCPI) des mesures inter-canal (CH2 vs CH1)."""
    return list(CMD.MEAS_TYPES_INTER_CHANNEL)
