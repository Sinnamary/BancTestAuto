"""
Parsing des données forme d'onde DOS1102.
- Réponse :WAV:DATA:ALL? (ASCII) : parse_ascii_waveform.
- Réponse :DATA:WAVE:SCREen:HEAD? + :DATA:WAVE:SCREEN:CHn? (binaire Hanmatek/OWON) :
  decode_screen_channel, time_base_from_meta, decode_screen_waveform.
Réutilisable sans UI (affichage courbe, export, analyse).
"""
import re
from typing import Any, Union


def _get_scale_from_meta(meta: dict[str, Any], ch: int) -> float:
    """Extrait le facteur d'échelle (V/unité) pour le canal ch depuis meta (SCALE + PROBE)."""
    ch_idx = ch - 1
    scale_str = meta["CHANNEL"][ch_idx]["SCALE"]
    possible_units = ["kV", "kA", "mV", "mA", "V", "A"]
    ten_exp = {"kV": 3, "kA": 3, "mV": -3, "mA": -3, "V": 0, "A": 0}
    scale_val = 1.0
    for unit in possible_units:
        if unit in scale_str:
            num_str = scale_str.replace(unit, "").strip() or "1"
            try:
                scale_val = float(num_str) * (10 ** ten_exp[unit])
            except ValueError:
                scale_val = 10 ** ten_exp[unit]
            break
    else:
        try:
            scale_val = float(scale_str)
        except ValueError:
            scale_val = 1.0
    probe_str = meta["CHANNEL"][ch_idx].get("PROBE", "X1")
    probe = int(probe_str.replace("X", "").strip() or "1")
    return scale_val * probe


def decode_screen_channel(raw_bytes: bytes, meta: dict[str, Any], ch: int) -> list[float]:
    """
    Décode les données binaires d'un canal (:DATA:WAVE:SCREEN:CHn?).
    raw_bytes : 4 octets à ignorer + paires int16 signé little-endian.
    Retourne les tensions en volts (à la sonde).
    """
    data = []
    for idx in range(4, len(raw_bytes), 2):
        if idx + 2 > len(raw_bytes):
            break
        adc_val = int.from_bytes([raw_bytes[idx], raw_bytes[idx + 1]], "little", signed=True)
        data.append(adc_val)
    offset = int(meta["CHANNEL"][ch - 1]["OFFSET"])
    scale = _get_scale_from_meta(meta, ch)
    # Formule Hanmatek/OWON : 410 points par division, 8.25 offset points par valeur ADC
    return [scale * (dk - offset * 8.25) / 410 for dk in data]


def time_base_from_meta(meta: dict[str, Any]) -> list[float]:
    """
    Reconstruit le vecteur temps (en secondes) à partir des méta-données.
    Utilise SAMPLE.DATALEN, SAMPLE.SAMPLERATE, TIMEBASE.HOFFSET.
    """
    nbr_points = int(meta["SAMPLE"]["DATALEN"])
    sample_rate_str = meta["SAMPLE"]["SAMPLERATE"]
    sample_rate_str = sample_rate_str.replace("(", "").replace(")", "")
    possible_units = ["kS/s", "MS/s", "GS/s"]
    ten_exp = [3, 6, 9]
    sample_rate = 1.0
    for k, unit in enumerate(possible_units):
        if unit in sample_rate_str:
            sample_rate = float(sample_rate_str.replace(unit, "").strip()) * (10 ** ten_exp[k])
            break
    sample_time = 5.0 / sample_rate if sample_rate else 0.0
    offset = float(meta["TIMEBASE"].get("HOFFSET", 0))
    time_offset = -1 * offset * 2 * sample_time
    return [(k - nbr_points / 2) * sample_time - time_offset for k in range(nbr_points)]


def decode_screen_waveform(
    meta: dict[str, Any],
    raw_ch1: bytes,
    raw_ch2: bytes,
) -> tuple[list[float], list[float], list[float]]:
    """
    Décode méta + données CH1 et CH2 en vecteurs temps (s), tension CH1 (V), tension CH2 (V).
    """
    time_arr = time_base_from_meta(meta)
    ch1_arr = decode_screen_channel(raw_ch1, meta, 1)
    ch2_arr = decode_screen_channel(raw_ch2, meta, 2)
    return time_arr, ch1_arr, ch2_arr


def parse_ascii_waveform(data: Union[str, bytes]) -> list[float] | None:
    """
    Extrait une liste de nombres depuis la réponse ASCII (virgules, espaces, retours à la ligne).
    Si data est bytes, tente un decode UTF-8.
    Retourne None si données binaires non décodables ou aucune valeur trouvée.
    """
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8", errors="strict")
        except Exception:
            return None
    else:
        text = data
    parts = re.split(r"[\s,;]+", text.strip())
    values: list[float] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            values.append(float(p))
        except ValueError:
            continue
    return values if values else None


def waveform_display_summary(data: Union[str, bytes]) -> str:
    """
    Résumé pour affichage : texte brut ou "<binaire N octets>".
    """
    if isinstance(data, bytes):
        return f"<binaire {len(data)} octets>"
    return data if data else "—"
