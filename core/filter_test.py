"""
Orchestration banc filtre : balayage en fréquence, mesures Us, calculs gain.
Appelle Fy6900Protocol et Measurement ; n'implémente pas les protocoles.
"""
import math
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
    points_per_decade: int  # Nombre de points par décade (gamme ×10) ; le total est déduit
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
        on_stabilization_started: Optional[Callable[[], None]] = None,
        on_stabilization_ended: Optional[Callable[[], None]] = None,
    ) -> list[BodePoint]:
        """
        Effectue le balayage. Au démarrage : configure le générateur (sinusoïde WMW00, amplitude Ue×√2,
        offset 0 V, rapport cyclique 50 %, phase 0°) via Fy6900Protocol. Pour chaque point : fréquence (µHz 14 chiffres),
        sortie ON, attente settling_ms, mesure Us, calcul gain. Retourne la liste des BodePoint.
        """
        self._abort = False
        ue = self._config.ue_rms
        # Sinusoïde : Ue RMS → amplitude crête à crête pour le générateur
        # V_pp = 2 * V_peak = 2 * (V_rms * sqrt(2)) = 2*sqrt(2)*V_rms ≈ 2,828*V_rms (ex. 1 V RMS → 2,828 V pp)
        amplitude_pp = ue * 2 * (2 ** 0.5)

        ch = self._config.generator_channel
        # Nombre total de points : points_per_decade × nombre de décades (log10(f_max/f_min))
        f_min = self._config.f_min_hz
        f_max = self._config.f_max_hz
        if f_min <= 0 or f_max <= 0:
            decades = 1.0
        else:
            decades = math.log10(f_max / f_min)
        n_points = max(2, round(self._config.points_per_decade * decades))
        logger.debug("banc filtre: démarrage balayage voie=%s, f_min=%.2f Hz, f_max=%.2f Hz, points/decade=%s → %d points, Ue_rms=%.3f V → Ue_pp=%.3f V",
                     ch, f_min, f_max, self._config.points_per_decade, n_points, ue, amplitude_pp)
        self._measurement.set_voltage_ac()
        # Même ordre et mêmes classes que l'onglet Générateur : forme (WMW00), amplitude (V pp), offset, rapport cyclique, phase
        # Fréquence envoyée via set_frequency_hz (µHz, 14 chiffres) à chaque point.
        self._generator.set_waveform(0, channel=ch)  # 0 = sinusoïde (WMW00)
        self._generator.set_amplitude_peak_v(amplitude_pp, channel=ch)  # valeur crête à crête (comme l'onglet Générateur)
        self._generator.set_offset_v(0.0, channel=ch)
        self._generator.set_duty_cycle_percent(50.0, channel=ch)
        self._generator.set_phase_deg(0.0, channel=ch)

        freqs = sweep_frequencies(
            f_min,
            f_max,
            n_points,
            self._config.scale,
        )
        total = len(freqs)
        results: list[BodePoint] = []

        # Appliquer le premier stimulus (première fréquence, sortie ON), puis attendre 2 s de stabilisation
        # des appareils et du filtre avant de lancer les mesures et le balayage.
        if freqs:
            first_f = freqs[0]
            self._generator.set_frequency_hz(first_f, channel=ch)
            self._generator.set_output(True, channel=ch)
            logger.debug("banc filtre: premier stimulus appliqué (f=%.4f Hz), attente 2 s stabilisation", first_f)
            if on_stabilization_started:
                on_stabilization_started()
            time.sleep(2.0)
            if on_stabilization_ended:
                on_stabilization_ended()

        for i, f_hz in enumerate(freqs):
            if self._abort:
                break
            # À partir du 2e point : régler la nouvelle fréquence et attendre settling_ms avant de mesurer
            if i > 0:
                self._generator.set_frequency_hz(f_hz, channel=ch)
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
