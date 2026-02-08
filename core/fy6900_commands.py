"""
Format des commandes FY6900 (FeelTech).
WMF/WFF : fréquence en µHz (microhertz), 14 chiffres avec zéros à gauche (doc officielle).
  Ex. 1000 Hz → 1e9 µHz → WMF00010000000000.
WMA/WFA : amplitude en V, 3 décimales. WMO/WFO : 2 décimales.
"""
EOL = "\n"

# Fréquence : selon le protocole FY6900 Rev 1.8, WMF/WFF attendent une valeur en µHz sur 14 chiffres.
FREQ_DIGITS = 14


def _freq_hz_clamped(freq_hz: float) -> float:
    """Fréquence en Hz, bornée à >= 0."""
    return max(0.0, float(freq_hz))


def _freq_hz_to_uhz(freq_hz: float) -> int:
    """Convertit une fréquence Hz en valeur entière µHz (pour WMF/WFF)."""
    return int(round(_freq_hz_clamped(freq_hz) * 1_000_000))


def format_wmw(waveform: int) -> str:
    """Forme d'onde voie 1. Doc FY6900 : format WMWxx (2 chiffres). 0 = sinusoïde."""
    return f"WMW{waveform:02d}{EOL}"


def format_wfw(waveform: int) -> str:
    """Forme d'onde voie 2 (WFW). Format WFWxx (2 chiffres, doc FY6900)."""
    return f"WFW{waveform:02d}{EOL}"


def format_wmf_hz(freq_hz: float) -> str:
    """
    Fréquence voie 1 en Hz → WMF (valeur en µHz, 14 chiffres, doc FY6900).
    Ex: 1000 Hz → 1e9 µHz → WMF00010000000000
    """
    uhz = _freq_hz_to_uhz(freq_hz)
    return f"WMF{uhz:0{FREQ_DIGITS}d}{EOL}"


def format_wff_hz(freq_hz: float) -> str:
    """Fréquence voie 2 en Hz → WFF (valeur en µHz, 14 chiffres, doc FY6900)."""
    uhz = _freq_hz_to_uhz(freq_hz)
    return f"WFF{uhz:0{FREQ_DIGITS}d}{EOL}"


def format_wma(amplitude_v_peak: float) -> str:
    """Amplitude crête voie 1 en V, 3 décimales (ex. WMA1.414, WMA4.000)."""
    return f"WMA{amplitude_v_peak:.3f}{EOL}"


def format_wfa(amplitude_v_peak: float) -> str:
    """Amplitude crête voie 2 en V, 3 décimales (WFA)."""
    return f"WFA{amplitude_v_peak:.3f}{EOL}"


def format_wmo(offset_v: float) -> str:
    """Offset voie 1 en V."""
    return f"WMO{offset_v:.2f}{EOL}"


def format_wfo(offset_v: float) -> str:
    """Offset voie 2 en V (WFO)."""
    return f"WFO{offset_v:.2f}{EOL}"


def format_wmn(output_on: bool) -> str:
    """Sortie voie 1 ON (True) ou OFF (False). Commande WMN."""
    return f"WMN{1 if output_on else 0}{EOL}"


def format_wfn(output_on: bool) -> str:
    """Sortie voie 2 ON (True) ou OFF (False). Commande WFN (canal auxiliaire)."""
    return f"WFN{1 if output_on else 0}{EOL}"


def format_wmd(duty_percent: float) -> str:
    """Rapport cyclique voie 1 en % (0–100). WMD."""
    v = max(0.0, min(100.0, float(duty_percent)))
    return f"WMD{v:.2f}{EOL}"


def format_wfd(duty_percent: float) -> str:
    """Rapport cyclique voie 2 en % (0–100). WFD."""
    v = max(0.0, min(100.0, float(duty_percent)))
    return f"WFD{v:.2f}{EOL}"


def format_wmp(phase_deg: float) -> str:
    """Phase voie 1 en degrés (0–360). WMP."""
    v = float(phase_deg) % 360.0
    return f"WMP{v:.2f}{EOL}"


def format_wfp(phase_deg: float) -> str:
    """Phase voie 2 en degrés (0–360). WFP."""
    v = float(phase_deg) % 360.0
    return f"WFP{v:.2f}{EOL}"
