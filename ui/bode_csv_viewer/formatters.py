"""
Formatage des valeurs pour l'affichage (fréquence, etc.). Partagé par le dialog et les viz.
"""


def format_freq_hz(hz: float) -> str:
    """Formate une fréquence en Hz pour l'affichage (ex. 1234.5 -> '1.23 kHz')."""
    if hz >= 1000:
        return f"{hz / 1000:.2f} kHz"
    if hz < 1 and hz > 0:
        return f"{hz * 1000:.1f} mHz"
    return f"{hz:.1f} Hz"
