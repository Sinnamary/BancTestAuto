"""
Génération de la liste de fréquences pour le balayage (log ou lin).
Pur calcul ; utilisé par filter_test.
"""
import math


def sweep_frequencies(
    f_min_hz: float,
    f_max_hz: float,
    n_points: int,
    scale: str = "log",
) -> list[float]:
    """
    Retourne une liste de n_points fréquences entre f_min_hz et f_max_hz.
    scale: "log" → échelle logarithmique (Bode) ; "lin" → linéaire.
    """
    if n_points <= 0:
        return []
    if n_points == 1:
        return [f_min_hz]

    if scale == "log":
        if f_min_hz <= 0 or f_max_hz <= 0:
            return []
        log_min = math.log10(f_min_hz)
        log_max = math.log10(f_max_hz)
        return [
            10 ** (log_min + (log_max - log_min) * i / (n_points - 1))
            for i in range(n_points)
        ]

    # linéaire
    step = (f_max_hz - f_min_hz) / (n_points - 1)
    return [f_min_hz + i * step for i in range(n_points)]
