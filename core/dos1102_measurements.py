"""
Helpers pour les mesures DOS1102 : formatage des résultats, calcul de phase.
Réutilisable sans UI (ex. banc filtre Bode phase, scripts).
"""
import json
import re

from . import dos1102_commands as CMD


def format_meas_general_response(raw: str | bytes) -> str:
    """
    Formate la réponse brute de :MEAS? pour affichage lisible.
    Corrige les problèmes d'encodage et tente un affichage structuré (JSON ou paires clé:valeur).
    """
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return "—"
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = raw.decode("latin-1", errors="replace")
    else:
        text = "".join(c if ord(c) < 0x110000 else "\uFFFD" for c in str(raw))
    text = text.strip()
    if not text:
        return "—"
    # Essai parsing JSON (réponse possible du type {"CH1":{"PERiod":"?,OFF",...}} ou chaîne)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            lines = []
            for key, val in data.items():
                if isinstance(val, dict):
                    lines.append(f"{key}:")
                    for k2, v2 in val.items():
                        lines.append(f"  {k2}: {v2}")
                else:
                    lines.append(f"{key}: {val}")
            return "\n".join(lines) if lines else text
    except (json.JSONDecodeError, TypeError):
        pass
    # Essai extraction de paires "key": "value" ou "key": "value"
    parts = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', text)
    if parts:
        return "\n".join(f"{k}: {v}" for k, v in parts)
    # Sinon découper par virgules pour aérer (garde les lignes courtes)
    if len(text) > 80 and "," in text:
        return "\n".join(s.strip() for s in text.split(",") if s.strip())
    return text


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
