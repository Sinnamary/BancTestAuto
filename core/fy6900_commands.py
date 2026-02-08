"""
Format des commandes FY6900 (FeelTech).
WMF/WFF : fréquence en Hz avec 6 décimales (ex. 12345678.901234).
WMA/WFA : amplitude en V, 2 décimales (ex. WMA5.00). WMO/WFO : 2 décimales.
"""
EOL = "\n"


def _freq_hz_clamped(freq_hz: float) -> float:
    """Fréquence en Hz, bornée à >= 0."""
    return max(0.0, float(freq_hz))


def format_wmw(waveform: int) -> str:
    """Forme d'onde voie 1. WMW0 = sinusoïde."""
    return f"WMW{waveform}{EOL}"


def format_wfw(waveform: int) -> str:
    """Forme d'onde voie 2 (WFW)."""
    return f"WFW{waveform}{EOL}"


def format_wmf_hz(freq_hz: float) -> str:
    """
    Fréquence voie 1 en Hz → WMF (Hz avec 6 décimales).
    Ex: 12345678.901234 → WMF12345678.901234
    """
    return f"WMF{_freq_hz_clamped(freq_hz):.6f}{EOL}"


def format_wff_hz(freq_hz: float) -> str:
    """Fréquence voie 2 en Hz → WFF (Hz avec 6 décimales)."""
    return f"WFF{_freq_hz_clamped(freq_hz):.6f}{EOL}"


def format_wma(amplitude_v_peak: float) -> str:
    """Amplitude crête voie 1 en V, 2 décimales (ex. WMA5.00)."""
    return f"WMA{amplitude_v_peak:.2f}{EOL}"


def format_wfa(amplitude_v_peak: float) -> str:
    """Amplitude crête voie 2 en V, 2 décimales (WFA)."""
    return f"WFA{amplitude_v_peak:.2f}{EOL}"


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
