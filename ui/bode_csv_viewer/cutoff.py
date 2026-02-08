"""
Détection de la fréquence de coupure -3 dB. Logique propre au viewer CSV.
"""
import math
from dataclasses import dataclass
from typing import List, Optional

from .model import BodeCsvDataset


@dataclass
class CutoffResult:
    """Résultat de la recherche de fc à -3 dB."""
    fc_hz: float
    gain_db: float


class Cutoff3DbFinder:
    """Recherche le premier point sous (gain_ref - 3 dB) avec interpolation log."""
    THRESHOLD_DB = 3.0

    def find(self, dataset: BodeCsvDataset, gain_ref: Optional[float] = None) -> Optional[CutoffResult]:
        freqs = dataset.freqs_hz()
        gains = dataset.gains_db()
        if not freqs or not gains or len(freqs) != len(gains):
            return None
        if gain_ref is None:
            gain_ref = max(gains)
        threshold = gain_ref - self.THRESHOLD_DB
        for i in range(len(gains)):
            if gains[i] <= threshold:
                if i == 0:
                    return CutoffResult(freqs[0], gains[0])
                f0, f1 = freqs[i - 1], freqs[i]
                g0, g1 = gains[i - 1], gains[i]
                if g1 == g0:
                    return CutoffResult(f0, g0)
                t = (threshold - g0) / (g1 - g0)
                log_fc = math.log10(f0) + t * (math.log10(f1) - math.log10(f0))
                fc = 10 ** log_fc
                return CutoffResult(fc, threshold)
        return None
