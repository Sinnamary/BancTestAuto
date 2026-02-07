"""
Calculs gain linéaire et gain dB (20×log₁₀(Us/Ue)).
Réutilisable sans UI ; utilisé par filter_test et bode_plot_widget.
"""
import math


def gain_linear(us: float, ue: float) -> float:
    """Gain linéaire Us/Ue. Si ue == 0, retourne 0."""
    if ue == 0:
        return 0.0
    return us / ue


def gain_db(us: float, ue: float) -> float:
    """
    20×log₁₀(Us/Ue) en dB.
    Si us <= 0, retourne une valeur très négative (ex. -200 dB).
    """
    g = gain_linear(us, ue)
    if g <= 0:
        return -200.0  # limite pratique pour éviter -inf
    return 20.0 * math.log10(g)
