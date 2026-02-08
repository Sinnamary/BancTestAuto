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
        """Première fréquence de coupure à -3 dB (ex. filtre passe-bas)."""
        all_cutoffs = self.find_all(dataset, gain_ref)
        return all_cutoffs[0] if all_cutoffs else None

    def find_all(
        self, dataset: BodeCsvDataset, gain_ref: Optional[float] = None
    ) -> List[CutoffResult]:
        """
        Toutes les fréquences où la courbe coupe le niveau gain_ref - 3 dB.
        Utile pour passe-bas (1 fc), coupe-bande (2 fc), etc.
        """
        freqs = dataset.freqs_hz()
        gains = dataset.gains_db()
        if not freqs or not gains or len(freqs) != len(gains):
            return []
        if gain_ref is None:
            gain_ref = max(gains)
        threshold = gain_ref - self.THRESHOLD_DB
        results: List[CutoffResult] = []
        for i in range(1, len(gains)):
            g0, g1 = gains[i - 1], gains[i]
            # Croisement : de part et d'autre du seuil
            if (g0 - threshold) * (g1 - threshold) > 0:
                continue
            if g1 == g0:
                fc = freqs[i - 1]
            else:
                f0, f1 = freqs[i - 1], freqs[i]
                t = (threshold - g0) / (g1 - g0)
                log_fc = math.log10(f0) + t * (math.log10(f1) - math.log10(f0))
                fc = 10 ** log_fc
            results.append(CutoffResult(fc_hz=fc, gain_db=threshold))
        return results
