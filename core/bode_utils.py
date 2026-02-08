"""
Utilitaires pour la visualisation Bode : lissage, détection de la fréquence de coupure.
"""
from typing import List, Optional, Tuple


def moving_average_smooth(values: List[float], window: int) -> List[float]:
    """
    Lissage par moyenne glissante centrée (fenêtre 3 à 11 points).
    Aux bords, la fenêtre est réduite pour ne pas dépasser.
    """
    n = len(values)
    if n == 0 or window < 1:
        return list(values)
    window = min(window, n)
    if window == 1:
        return list(values)
    half = window // 2
    result = []
    for i in range(n):
        start = max(0, i - half)
        end = min(n, i + half + 1)
        slice_vals = values[start:end]
        result.append(sum(slice_vals) / len(slice_vals))
    return result


def find_cutoff_3db(
    freqs: List[float],
    gains_db: List[float],
    gain_ref: Optional[float] = None,
) -> Optional[Tuple[float, float]]:
    """
    Recherche la fréquence de coupure à -3 dB (premier point sous gain_ref - 3 dB).
    gain_ref : gain de référence (bande passante). Si None, pris comme le max des gains.
    Retourne (f_c_hz, gain_at_fc_db) ou None si non trouvé.
    """
    if not freqs or not gains_db or len(freqs) != len(gains_db):
        return None
    if gain_ref is None:
        gain_ref = max(gains_db)
    threshold = gain_ref - 3.0
    for i in range(len(gains_db)):
        if gains_db[i] <= threshold:
            if i == 0:
                return (freqs[0], gains_db[0])
            # Interpolation linéaire en log(f) pour estimer fc
            f0, f1 = freqs[i - 1], freqs[i]
            g0, g1 = gains_db[i - 1], gains_db[i]
            if g1 == g0:
                return (f0, g0)
            t = (threshold - g0) / (g1 - g0)
            import math
            log_f0 = math.log10(f0)
            log_f1 = math.log10(f1)
            log_fc = log_f0 + t * (log_f1 - log_f0)
            fc = 10 ** log_fc
            gain_at_fc = threshold
            return (fc, gain_at_fc)
    return None


def find_peaks_and_valleys(
    freqs: List[float],
    gains_db: List[float],
    order: int = 3,
) -> List[Tuple[float, float, str]]:
    """
    Détection des maxima et minima locaux (ordre = nombre de points de chaque côté).
    Retourne une liste de (f_hz, gain_db, "pic"|"creux").
    """
    n = len(freqs)
    if n < 2 * order + 1:
        return []
    result = []
    for i in range(order, n - order):
        window_gains = gains_db[i - order : i + order + 1]
        if gains_db[i] == max(window_gains):
            result.append((freqs[i], gains_db[i], "pic"))
        elif gains_db[i] == min(window_gains):
            result.append((freqs[i], gains_db[i], "creux"))
    return result
