"""
Génération de la liste de fréquences pour le balayage (log ou lin).
Pur calcul ; utilisé par filter_test.

En échelle log : répartition avec un **nombre identique de points par décade**
(chaque gamme ×10, ex. 10–100 Hz, 100–1000 Hz) pour une lecture Bode homogène.
Les fréquences sont calculées exactement (pas d'arrondi) pour respecter le nombre de points par décade.
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

    - scale "log" : échelle logarithmique. Les points sont répartis de façon à
      avoir **exactement le même nombre de points dans chaque décade** (chaque gamme ×10).
    - scale "lin" : répartition linéaire (pas constant en Hz).
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

    # linéaire : pas constant en Hz
    step = (f_max_hz - f_min_hz) / (n_points - 1)
    return [f_min_hz + i * step for i in range(n_points)]
