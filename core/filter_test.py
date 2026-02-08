"""
Orchestration banc filtre : balayage en fréquence, mesures Us, calculs gain.
Appelle Fy6900Protocol et Measurement ; n'implémente pas les protocoles.
"""
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .fy6900_protocol import Fy6900Protocol
from .measurement import Measurement
from .filter_sweep import sweep_frequencies
from .bode_calc import gain_linear, gain_db
from .app_logger import get_logger

logger = get_logger(__name__)


@dataclass
class BodePoint:
    """Un point du diagramme de Bode."""
    f_hz: float
    us_v: float
    gain_linear: float
    gain_db: float


@dataclass
class FilterTestConfig:
    """Paramètres du balayage (depuis config ou interface)."""
    generator_channel: int
    f_min_hz: float
    f_max_hz: float
    n_points: int
    scale: str  # "log" | "lin"
    settling_ms: int
    ue_rms: float


class FilterTest:
    """
    Banc de test filtre : applique la config connue, balaie les fréquences,
    mesure Us, calcule gain linéaire et dB. Émet la progression via callback.
    """

    def __init__(
        self,
        generator: Fy6900Protocol,
        measurement: Measurement,
        config: FilterTestConfig,
    ):
        self._generator = generator
        self._measurement = measurement
        self._config = config
        self._abort = False

    def set_config(self, config: FilterTestConfig) -> None:
        self._config = config

    def abort(self) -> None:
        self._abort = True

    def run_sweep(
        self,
        on_point: Optional[Callable[[BodePoint, int, int], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> list[BodePoint]:
        """
        Effectue le balayage. Pour chaque point :
        - configure le générateur (sinusoïde, Ue, fréquence), sortie ON ;
        - attend settling_ms ;
        - mesure Us ;
        - calcule gain et appelle on_point(result, index, total) puis on_progress(index+1, total).
        Retourne la liste des BodePoint. Si abort() a été appelé, arrête et retourne les points déjà acquis.
        """
        self._abort = False
        ue = self._config.ue_rms
        # Amplitude crête pour 1 V RMS : sqrt(2)
        amplitude_peak = ue * (2 ** 0.5)

        ch = self._config.generator_channel
        logger.debug("banc filtre: démarrage balayage voie=%s, f_min=%.2f Hz, f_max=%.2f Hz, n_points=%s, Ue_rms=%.3f V",
                     ch, self._config.f_min_hz, self._config.f_max_hz, self._config.n_points, ue)
        self._measurement.set_voltage_ac()
        self._generator.set_waveform(0, channel=ch)
        self._generator.set_amplitude_peak_v(amplitude_peak, channel=ch)
        self._generator.set_offset_v(0.0, channel=ch)

        freqs = sweep_frequencies(
            self._config.f_min_hz,
            self._config.f_max_hz,
            self._config.n_points,
            self._config.scale,
        )
        total = len(freqs)
        results: list[BodePoint] = []

        for i, f_hz in enumerate(freqs):
            if self._abort:
                break
            self._generator.set_frequency_hz(f_hz, channel=ch)
            self._generator.set_output(True, channel=ch)
            time.sleep(self._config.settling_ms / 1000.0)

            raw = self._measurement.read_value()
            us = self._measurement.parse_float(raw)
            if us is None:
                us = 0.0
            g_lin = gain_linear(us, ue)
            g_db = gain_db(us, ue)
            logger.debug("banc filtre point %d/%d: f=%.4f Hz, Us=%r -> %.4f V, gain_lin=%.4f, gain_dB=%.2f",
                         i + 1, total, f_hz, raw, us, g_lin, g_db)
            point = BodePoint(f_hz=f_hz, us_v=us, gain_linear=g_lin, gain_db=g_db)
            results.append(point)
            if on_point:
                on_point(point, i, total)
            if on_progress:
                on_progress(i + 1, total)

        self._generator.set_output(False, channel=self._config.generator_channel)
        logger.debug("banc filtre: balayage terminé, %d points", len(results))
        return results
