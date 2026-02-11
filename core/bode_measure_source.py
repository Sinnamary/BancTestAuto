"""
Source de mesure pour le banc filtre Bode : abstraction multimètre / oscilloscope.
Permet au FilterTest d'utiliser soit le multimètre (Us seul, Ue nominal), soit
l'oscilloscope (Ue Ch1, Us Ch2, phase Ch2 vs Ch1).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Protocol, Tuple

from .app_logger import get_logger
from .dos1102_measurements import phase_deg_from_delay

if TYPE_CHECKING:
    from .dos1102_protocol import Dos1102Protocol
    from .measurement import Measurement

logger = get_logger(__name__)


def _parse_float(s: Optional[str]) -> Optional[float]:
    """Parse une chaîne en float (réponse SCPI). Retourne None si invalide."""
    if s is None or not (s := str(s).strip()):
        return None
    try:
        return float(s.replace(",", "."))
    except (ValueError, TypeError):
        return None


class BodeMeasureSource(Protocol):
    """
    Interface pour une source de mesure du banc filtre.
    - prepare_for_sweep() : configuration avant le balayage (ex. mode AC multimètre).
    - read_ue_us_phase(ue_nominal) : lit (Ue, Us, phase_deg ou None).
    """

    def prepare_for_sweep(self) -> None:
        """Configure la source avant le balayage (ex. mode tension AC)."""
        ...

    def read_ue_us_phase(self, ue_nominal: float) -> Tuple[float, float, Optional[float]]:
        """
        Lit Ue (V RMS), Us (V RMS) et éventuellement la phase (deg, Ch2 vs Ch1).
        Pour le multimètre, Ue = ue_nominal (non mesuré), phase = None.
        Retourne (ue_rms, us_rms, phase_deg | None).
        """
        ...


class MultimeterBodeAdapter:
    """
    Adaptateur du multimètre OWON pour le banc filtre.
    Ue = valeur nominale (config), Us = lecture MEAS?, pas de phase.
    """

    def __init__(self, measurement: "Measurement") -> None:
        self._measurement = measurement

    def prepare_for_sweep(self) -> None:
        self._measurement.set_voltage_ac()

    def read_ue_us_phase(self, ue_nominal: float) -> Tuple[float, float, Optional[float]]:
        raw = self._measurement.read_value()
        us = self._measurement.parse_float(raw)
        if us is None:
            us = 0.0
        return (ue_nominal, us, None)


class OscilloscopeBodeSource:
    """
    Source de mesure Bode via oscilloscope DOS1102 : Ue (Ch1 RMS), Us (Ch2 RMS),
    phase (Ch2 vs Ch1) en degrés.
    """

    def __init__(
        self,
        protocol: "Dos1102Protocol",
        channel_ue: int = 1,
        channel_us: int = 2,
    ) -> None:
        self._protocol = protocol
        self._channel_ue = channel_ue
        self._channel_us = channel_us

    def prepare_for_sweep(self) -> None:
        """Aucune config spécifique requise pour le sweep (mesures à la demande)."""
        pass

    def read_ue_us_phase(self, ue_nominal: float) -> Tuple[float, float, Optional[float]]:
        """
        Lit CYCRms sur canal Ue, CYCRms sur canal Us, puis période (PERiod) sur canal Ue
        et délai phase (RISEPHASEDELAY) sur canal Us pour calculer la phase.
        """
        # CYCRms = RMS sur un cycle (sinusoïde → valeur efficace)
        ue_rms = _parse_float(self._protocol.meas_ch(self._channel_ue, "CYCRms"))
        us_rms = _parse_float(self._protocol.meas_ch(self._channel_us, "CYCRms"))
        period_s = _parse_float(self._protocol.meas_ch(self._channel_ue, "PERiod"))
        delay_s = _parse_float(self._protocol.meas_ch(self._channel_us, "RISEPHASEDELAY"))

        ue = float(ue_rms) if ue_rms is not None else ue_nominal
        us = float(us_rms) if us_rms is not None else 0.0
        phase = phase_deg_from_delay(delay_s, period_s) if (delay_s is not None and period_s is not None) else None

        if ue_rms is None or us_rms is None:
            logger.debug("bode oscillo: Ue=%s Us=%s (période=%s, délai=%s) -> phase=%s", ue_rms, us_rms, period_s, delay_s, phase)
        return (ue, us, phase)


class SwitchableBodeMeasureSource:
    """
    Source de mesure commutable : multimètre ou oscilloscope.
    Utilisé par le bridge pour fournir une seule instance à FilterTest ;
    la vue (ou le bridge) appelle set_source() pour choisir la source active.
    """

    SOURCE_MULTIMETER = "multimeter"
    SOURCE_OSCILLOSCOPE = "oscilloscope"

    def __init__(
        self,
        multimeter_source: BodeMeasureSource,
        get_oscilloscope_source: Callable[[], Optional["BodeMeasureSource"]],
    ) -> None:
        self._multimeter_source = multimeter_source
        self._get_oscilloscope_source = get_oscilloscope_source
        self._current: str = self.SOURCE_MULTIMETER
        self._oscilloscope_source: Optional[BodeMeasureSource] = None

    def set_source(self, source: str) -> bool:
        """
        Bascule sur 'multimeter' ou 'oscilloscope'. Retourne True si le changement
        a été appliqué, False si oscilloscope demandé mais indisponible (reste sur multimètre).
        """
        if source == self.SOURCE_OSCILLOSCOPE:
            if self._oscilloscope_source is None:
                self._oscilloscope_source = self._get_oscilloscope_source()
            if self._oscilloscope_source is None:
                logger.warning("SwitchableBodeMeasureSource: oscilloscope demandé mais source indisponible (non connecté?)")
                return False
            self._current = self.SOURCE_OSCILLOSCOPE
            return True
        self._current = self.SOURCE_MULTIMETER
        return True

    def get_current_source(self) -> str:
        return self._current

    def prepare_for_sweep(self) -> None:
        if self._current == self.SOURCE_OSCILLOSCOPE and self._oscilloscope_source is not None:
            self._oscilloscope_source.prepare_for_sweep()
        else:
            self._multimeter_source.prepare_for_sweep()

    def read_ue_us_phase(self, ue_nominal: float) -> Tuple[float, float, Optional[float]]:
        if self._current == self.SOURCE_OSCILLOSCOPE and self._oscilloscope_source is not None:
            return self._oscilloscope_source.read_ue_us_phase(ue_nominal)
        return self._multimeter_source.read_ue_us_phase(ue_nominal)
