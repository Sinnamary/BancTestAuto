"""
Format des commandes FY6900 (FeelTech).
WMF : 14 chiffres en µHz ; WMA, WMO : valeur décimale. Aucune I/O.
"""
EOL = "\n"


def format_wmw(waveform: int) -> str:
    """Forme d'onde canal principal. WMW0 = sinusoïde."""
    return f"WMW{waveform}{EOL}"


def format_wmf_hz(freq_hz: float) -> str:
    """
    Fréquence en Hz → commande WMF (14 chiffres, unité µHz).
    Ex: 100 Hz → WMF00100000000 + LF
    """
    micro_hz = int(freq_hz * 1_000_000)
    micro_hz = max(0, min(99999999999999, micro_hz))
    return f"WMF{micro_hz:014d}{EOL}"


def format_wma(amplitude_v_peak: float) -> str:
    """Amplitude crête en V. Ex: 1.414 pour 1 V RMS sinusoïdal."""
    return f"WMA{amplitude_v_peak:.3f}{EOL}"


def format_wmo(offset_v: float) -> str:
    """Offset en V."""
    return f"WMO{offset_v:.2f}{EOL}"


def format_wmn(output_on: bool) -> str:
    """Sortie ON (True) ou OFF (False)."""
    return f"WMN{1 if output_on else 0}{EOL}"
