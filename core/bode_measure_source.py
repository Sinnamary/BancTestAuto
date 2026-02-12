"""
Source de mesure pour le banc filtre Bode : abstraction multimètre / oscilloscope.
Permet au FilterTest d'utiliser soit le multimètre (Us seul, Ue nominal), soit
l'oscilloscope (Ue Ch1, Us Ch2, phase Ch2 vs Ch1).
"""
from __future__ import annotations

import math
import re
import time
from typing import TYPE_CHECKING, Callable, Optional, Protocol, Tuple

from .app_logger import get_logger
from .dos1102_measurements import phase_deg_from_delay

if TYPE_CHECKING:
    from .dos1102_protocol import Dos1102Protocol
    from .measurement import Measurement

logger = get_logger(__name__)

# Calibres verticaux DOS1102 (V/div) : du plus sensible au moins sensible pour maximiser la précision
_OSC_V_SCALES_V_PER_DIV = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0)

# Base de temps DOS1102 (s/div) : plage complète 2 ns à 1000 s (capacité de l'oscilloscope)
_OSC_TIME_SCALES_S_PER_DIV = (
    2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9,
    1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,
    1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3,
    1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0,
)


def _time_scale_for_frequency(f_hz: float) -> float:
    """
    Retourne le time/div (s/div) adapté à la fréquence pour afficher ~2 à 4 périodes sur l'écran.
    Choisit le calibre le plus proche dans la liste autorisée.
    """
    if f_hz <= 0:
        return _OSC_TIME_SCALES_S_PER_DIV[-1]
    period = 1.0 / f_hz
    # ~3 périodes sur 10 divisions → time_per_div idéal = period * 0.3
    ideal = period * 0.3
    best = _OSC_TIME_SCALES_S_PER_DIV[0]
    for s in _OSC_TIME_SCALES_S_PER_DIV:
        if s >= ideal:
            return s
        best = s
    return best


def _scale_for_rms_voltage(v_rms: float) -> float:
    """
    Retourne le calibre (V/div) adapté à une tension RMS pour maximiser la précision.
    Le signal crête-à-crête (2*sqrt(2)*V_rms) doit tenir dans l'écran (~8 div) sans saturer.
    On choisit le calibre le plus sensible (plus petit) qui permet de ne pas clipser.
    """
    if v_rms <= 0:
        return _OSC_V_SCALES_V_PER_DIV[0]
    v_pp = 2.0 * math.sqrt(2.0) * v_rms
    min_scale = v_pp / 8.0  # au moins 8 divisions pour le pic-à-pic
    for s in _OSC_V_SCALES_V_PER_DIV:
        if s >= min_scale:
            return s
    return _OSC_V_SCALES_V_PER_DIV[-1]


def _parse_float(s: Optional[str]) -> Optional[float]:
    """Parse une chaîne en float (réponse SCPI). Retourne None si invalide."""
    if s is None or not (s := str(s).strip()):
        return None
    try:
        return float(s.replace(",", "."))
    except (ValueError, TypeError):
        return None


def _parse_dos1102_value(raw: Optional[str]) -> Optional[float]:
    """
    Parse une réponse DOS1102 au format "Label : value" (ex. "TR : 1.234", "T : 0.001").
    Retourne le nombre extrait, ou None si invalide / "?".
    """
    if raw is None or not (s := str(raw).strip()):
        return None
    # Format "XX : value" ou "value" seul (ex. "Vpp : 2.266V", "T :   ?")
    if ":" in s:
        s = s.split(":")[-1].strip()
    s = s.replace(",", ".")
    # Retirer symboles et unités en fin (°, V, s, etc.) pour extraire le nombre
    s = re.sub(r"[\u00b0°\s]*[A-Za-z]*\s*$", "", s).strip()
    if not s or s == "?":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_dos1102_voltage(raw: Optional[str]) -> Optional[float]:
    """
    Parse une réponse DOS1102 contenant une tension et retourne la valeur en Volts.
    L'oscilloscope envoie l'unité dans le log (ex. "TR : 673.7mV", "TR : 999.2mV") :
    si la réponse contient "mV", on convertit en V (÷ 1000) pour le tableau.
    Si "V" sans "mV" (ex. "2.266V") → valeur déjà en V. Si unité absente et valeur > 100, suppose mV.
    """
    val = _parse_dos1102_value(raw)
    if val is None:
        return None
    s = (raw or "").strip()
    if "mv" in s.lower():
        return val / 1000.0
    if "v" in s.lower():
        return val  # déjà en V (ex. "2.266V")
    # Unité absente : valeur > 100 typique de mV (ex. 775 mV)
    if val > 100:
        return val / 1000.0
    return val


def _pkpk_to_rms_sinusoidal(v_pp: float) -> float:
    """Convertit tension crête-à-crête (V) en RMS pour un signal sinusoïdal : V_rms = V_pp / (2*sqrt(2))."""
    return v_pp / (2.0 * math.sqrt(2.0))


# Caractères pouvant indiquer des degrés (° peut arriver en \xb0 Latin-1 → \ufffd en UTF-8)
_DEGREE_INDICATORS = ("\u00b0", "°", "\ufffd")


def _parse_dos1102_phase(raw: Optional[str]) -> Tuple[Optional[float], bool]:
    """
    Parse la réponse à :MEAS:CH2:RISEPHASEDELAY?.
    Le DOS1102 renvoie la phase directement en degrés (ex. "RP : 26.352°").
    Le ° est parfois reçu en Latin-1 (\\xb0) et devient \\ufffd en UTF-8 : on le reconnaît quand même.
    Retourne (valeur, is_degrees).
    """
    if raw is None or not (s := str(raw).strip()):
        return None, False
    if ":" in s:
        s = s.split(":")[-1].strip()
    s = s.replace(",", ".")
    is_degrees = any(c in s for c in _DEGREE_INDICATORS)
    # Extraire uniquement le nombre (évite float() sur "29.520\\ufffd" ou "29.520°")
    num_match = re.search(r"[-+]?\d*\.?\d+", s)
    if not num_match:
        return None, False
    try:
        val = float(num_match.group())
    except (ValueError, TypeError):
        return None, False
    # Valeur typique en degrés (-360..360) : considérer comme degrés si symbole présent ou plage cohérente
    if not is_degrees and -360 <= val <= 360:
        is_degrees = True
    return val, is_degrees


class BodeMeasureSource(Protocol):
    """
    Interface pour une source de mesure du banc filtre.
    - prepare_for_sweep() : configuration avant le balayage (ex. mode AC multimètre).
    - read_ue_us_phase(ue_nominal) : lit (Ue, Us, phase_deg ou None).
    """

    def prepare_for_sweep(self) -> None:
        """Configure la source avant le balayage (ex. mode tension AC)."""
        ...

    def read_ue_us_phase(
        self,
        ue_nominal: float,
        prev_ue: Optional[float] = None,
        prev_us: Optional[float] = None,
        freq_hz: Optional[float] = None,
    ) -> Tuple[float, float, Optional[float]]:
        """
        Lit Ue (V RMS), Us (V RMS) et éventuellement la phase (deg, Ch2 vs Ch1).
        prev_ue / prev_us : tensions du point précédent (optionnel) pour adapter les calibres.
        freq_hz : fréquence du générateur (optionnel) pour adapter la base de temps de l'oscilloscope.
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

    def prepare_first_point(self, freq_hz: float) -> None:
        """Rien à faire pour le multimètre (pas de base de temps / calibres à régler)."""
        pass

    def read_ue_us_phase(
        self,
        ue_nominal: float,
        prev_ue: Optional[float] = None,
        prev_us: Optional[float] = None,
        freq_hz: Optional[float] = None,
    ) -> Tuple[float, float, Optional[float]]:
        raw = self._measurement.read_value()
        us = self._measurement.parse_float(raw)
        if us is None:
            us = 0.0
        return (ue_nominal, us, None)

    def end_of_sweep(self) -> None:
        """Rien à faire pour le multimètre."""
        pass


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
        phase_skip_below_scale_ch2_mv: float = 20,
    ) -> None:
        self._protocol = protocol
        self._channel_ue = channel_ue
        self._channel_us = channel_us
        # Calibre CH2 (mV/div) en dessous duquel on ne relève plus la phase (lue depuis config filter_test)
        self._phase_skip_below_scale_ch2_mv = float(phase_skip_below_scale_ch2_mv)
        self._first_point_prepared = False

    def prepare_first_point(self, freq_hz: float) -> None:
        """
        Met l'outil de mesure en condition pour le premier point (base de temps + calibres)
        avant la temporisation de 2 s. Appelé après mise sous tension du générateur.
        """
        if freq_hz is None or freq_hz <= 0:
            return
        time_per_div = _time_scale_for_frequency(freq_hz)
        self._protocol.set_hor_scale(time_per_div)
        if time_per_div >= 1:
            logger.debug("Oscilloscope prepare_first_point: base de temps %.2f s/div (f=%.2f Hz)", time_per_div, freq_hz)
        elif time_per_div >= 1e-3:
            logger.debug("Oscilloscope prepare_first_point: base de temps %.2f ms/div (f=%.2f Hz)", time_per_div * 1e3, freq_hz)
        elif time_per_div >= 1e-6:
            logger.debug("Oscilloscope prepare_first_point: base de temps %.2f µs/div (f=%.2f Hz)", time_per_div * 1e6, freq_hz)
        else:
            logger.debug("Oscilloscope prepare_first_point: base de temps %.2f ns/div (f=%.2f Hz)", time_per_div * 1e9, freq_hz)
        scale_v = 0.5
        self._protocol.set_ch_scale(self._channel_ue, scale_v)
        self._protocol.set_ch_scale(self._channel_us, scale_v)
        logger.debug("Oscilloscope prepare_first_point: échelle CH1=CH2=500 mV/div, outil de mesure prêt pour 1er point")
        self._first_point_prepared = True

    def prepare_for_sweep(self) -> None:
        """Couplage AC sur les deux voies (Ue=CH1, Us=CH2) pour mesurer le signal sans offset DC."""
        self._first_point_prepared = False
        self._protocol.set_ch1_coupling("AC")
        self._protocol.set_ch2_coupling("AC")
        logger.info("Oscilloscope: couplage CH1=AC, CH2=AC (début balayage)")
        time.sleep(0.05)

    def read_ue_us_phase(
        self,
        ue_nominal: float,
        prev_ue: Optional[float] = None,
        prev_us: Optional[float] = None,
        freq_hz: Optional[float] = None,
    ) -> Tuple[float, float, Optional[float]]:
        """
        Lit RMS (CYCRms puis TRUERMS en secours) et période sur chaque canal,
        et phase (RISEPHASEDELAY sur CH2). Les réponses DOS1102 au format
        "Label : value" ou "value°" sont parsées correctement.

        Commandes SCPI envoyées à l'oscilloscope (une par mesure) :
        - :MEAS:CH1:CYCRms?     (RMS canal 1, Ue) ; si invalide → PKPK? puis V_rms = V_pp/(2*sqrt(2))
        - :MEAS:CH1:PERiod?     (période canal 1, pour phase)
        - :MEAS:CH2:CYCRms?     (RMS canal 2, Us) ; si invalide → PKPK?
        - :MEAS:CH2:RISEPHASEDELAY? (phase CH2 vs CH1 : le DOS1102 renvoie directement des degrés, ex. "RP : 26.352°")
        """
        # Adapter la base de temps et les calibres (sauf si déjà fait par prepare_first_point avant la temporisation 2 s)
        if prev_ue is None and prev_us is None and self._first_point_prepared:
            scale_ch2_v_per_div = 0.5
            self._first_point_prepared = False
            logger.debug("Oscilloscope: 1er point — base de temps et calibres déjà en place (prepare_first_point), lecture directe")
        else:
            if freq_hz is not None and freq_hz > 0:
                time_per_div = _time_scale_for_frequency(freq_hz)
                self._protocol.set_hor_scale(time_per_div)
                if time_per_div >= 1:
                    logger.info("Oscilloscope: base de temps %.2f s/div (f=%.2f Hz)", time_per_div, freq_hz)
                elif time_per_div >= 1e-3:
                    logger.info("Oscilloscope: base de temps %.2f ms/div (f=%.2f Hz)", time_per_div * 1e3, freq_hz)
                elif time_per_div >= 1e-6:
                    logger.info("Oscilloscope: base de temps %.2f µs/div (f=%.2f Hz)", time_per_div * 1e6, freq_hz)
                else:
                    logger.info("Oscilloscope: base de temps %.2f ns/div (f=%.2f Hz)", time_per_div * 1e9, freq_hz)
                time.sleep(1.0)  # stabilisation au moins 1 s après changement de base de temps
            if prev_ue is None and prev_us is None:
                scale_v = 0.5
                scale_ch2_v_per_div = 0.5
                self._protocol.set_ch_scale(self._channel_ue, scale_v)
                self._protocol.set_ch_scale(self._channel_us, scale_v)
                logger.info("Oscilloscope: échelle CH1=CH2=500 mV/div (début balayage)")
                time.sleep(1.0)  # stabilisation 1 s après calibres pour que la 1re lecture soit correcte
            else:
                scale_ue = _scale_for_rms_voltage(prev_ue) if prev_ue is not None else 0.5
                scale_us = _scale_for_rms_voltage(prev_us) if prev_us is not None else 0.5
                scale_ch2_v_per_div = scale_us
                self._protocol.set_ch_scale(self._channel_ue, scale_ue)
                self._protocol.set_ch_scale(self._channel_us, scale_us)
                logger.info("Oscilloscope: échelle CH1=%.2f V/div, CH2=%.2f V/div (Ue=%.3f V, Us=%.3f V)", scale_ue, scale_us, prev_ue or 0, prev_us or 0)
                time.sleep(0.05)  # laisser l'oscilloscope appliquer les nouveaux calibres

        # En dessous du calibre configuré (ex. 20 mV/div), ne pas relever la phase (signal trop altéré)
        threshold_v = self._phase_skip_below_scale_ch2_mv / 1000.0
        skip_phase = scale_ch2_v_per_div <= threshold_v

        # Canal Ue (CH1) : RMS (CYCRms) puis PKPK puis TRUERMS si invalide ; tensions en V (mV → V si besoin)
        ue_rms_raw = self._protocol.meas_ch(self._channel_ue, "CYCRms")
        ue_rms = _parse_dos1102_voltage(ue_rms_raw)
        if ue_rms is None:
            ue_pp_raw = self._protocol.meas_ch(self._channel_ue, "PKPK")
            ue_pp = _parse_dos1102_voltage(ue_pp_raw)
            if ue_pp is not None and ue_pp > 0:
                ue_rms = _pkpk_to_rms_sinusoidal(ue_pp)
        if ue_rms is None:
            ue_tr_raw = self._protocol.meas_ch(self._channel_ue, "TRUERMS")
            ue_rms = _parse_dos1102_voltage(ue_tr_raw)
        period_s = _parse_dos1102_value(self._protocol.meas_ch(self._channel_ue, "PERiod"))

        # Canal Us (CH2) : idem CYCRms puis PKPK puis TRUERMS ; tensions en V
        us_rms_raw = self._protocol.meas_ch(self._channel_us, "CYCRms")
        us_rms = _parse_dos1102_voltage(us_rms_raw)
        us_pp_raw = None
        us_tr_raw = None
        if us_rms is None:
            us_pp_raw = self._protocol.meas_ch(self._channel_us, "PKPK")
            us_pp = _parse_dos1102_voltage(us_pp_raw)
            if us_pp is not None and us_pp >= 0:
                us_rms = _pkpk_to_rms_sinusoidal(us_pp)
        if us_rms is None:
            us_tr_raw = self._protocol.meas_ch(self._channel_us, "TRUERMS")
            us_rms = _parse_dos1102_voltage(us_tr_raw)
        if us_rms is None:
            logger.warning(
                "bode oscillo: CH2 (Us) tension non lue — CYCRms=%r, PKPK=%r, TRUERMS=%r. Vérifier couplage AC/DC et câblage CH2.",
                us_rms_raw, us_pp_raw, us_tr_raw,
            )
        # Phase : ne pas relever si calibre CH2 <= 20 mV/div (signal trop altéré)
        if skip_phase:
            phase_val, phase_in_degrees, delay_s = None, False, None
        else:
            phase_raw = self._protocol.meas_ch(self._channel_us, "RISEPHASEDELAY")
            phase_val, phase_in_degrees = _parse_dos1102_phase(phase_raw)
            delay_s = None if phase_in_degrees else phase_val

        ue = float(ue_rms) if ue_rms is not None else ue_nominal
        us = float(us_rms) if us_rms is not None else 0.0
        if skip_phase:
            phase = None
        elif phase_val is not None:
            if phase_in_degrees:
                phase = phase_val  # DOS1102 renvoie directement des degrés
            elif period_s is not None and period_s > 0 and delay_s is not None:
                phase = phase_deg_from_delay(delay_s, period_s)  # délai en s → °
            elif -360 <= phase_val <= 360:
                phase = phase_val  # valeur plausible en ° (ex. symbole ° perdu en encodage)
            else:
                phase = None
        else:
            phase = None

        if ue_rms is None or us_rms is None:
            logger.debug("bode oscillo: Ue=%s Us=%s (période=%s, phase_raw=%s) -> phase=%s", ue_rms, us_rms, period_s, phase_raw, phase)
        return (ue, us, phase)

    def end_of_sweep(self) -> None:
        """En fin de balayage : repasse les deux canaux sur 5 V/div."""
        self._protocol.set_ch_scale(self._channel_ue, 5.0)
        self._protocol.set_ch_scale(self._channel_us, 5.0)
        logger.info("Oscilloscope: échelle CH1=CH2=5 V/div (fin balayage)")


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

    def prepare_first_point(self, freq_hz: float) -> None:
        """Délègue à la source active (oscillo : base de temps + calibres ; multimètre : rien)."""
        if self._current == self.SOURCE_OSCILLOSCOPE and self._oscilloscope_source is not None:
            self._oscilloscope_source.prepare_first_point(freq_hz)
        else:
            self._multimeter_source.prepare_first_point(freq_hz)

    def read_ue_us_phase(
        self,
        ue_nominal: float,
        prev_ue: Optional[float] = None,
        prev_us: Optional[float] = None,
        freq_hz: Optional[float] = None,
    ) -> Tuple[float, float, Optional[float]]:
        if self._current == self.SOURCE_OSCILLOSCOPE and self._oscilloscope_source is not None:
            return self._oscilloscope_source.read_ue_us_phase(ue_nominal, prev_ue, prev_us, freq_hz)
        return self._multimeter_source.read_ue_us_phase(ue_nominal, prev_ue, prev_us, freq_hz)

    def end_of_sweep(self) -> None:
        """Délègue à la source active (oscillo : 5 V/div en fin ; multimètre : rien)."""
        if self._current == self.SOURCE_OSCILLOSCOPE and self._oscilloscope_source is not None:
            self._oscilloscope_source.end_of_sweep()
        else:
            self._multimeter_source.end_of_sweep()
