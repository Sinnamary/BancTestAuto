"""
Protocole FY6900 (FeelTech) : WMW, WMF, WMA, WMO, WMN.
Utilise SerialConnection ; appelé par generator_view et filter_test.

Documentation : le FY6900 renvoie 0x0a (LF) après exécution de chaque commande.
Il faut lire cette réponse avant d'envoyer la commande suivante (succession de commandes).
"""
from .serial_connection import SerialConnection
from . import fy6900_commands as FY
from .app_logger import get_logger

logger = get_logger(__name__)


class Fy6900Protocol:
    """
    Commandes FY6900 sur une liaison série.
    Débit 115200, fin de commande 0x0a (LF).
    Après chaque envoi, lecture de la réponse (0x0a) avant la commande suivante.
    """

    def __init__(self, connection: SerialConnection):
        self._conn = connection

    def _send(self, cmd: str) -> None:
        # cmd contient toujours EOL (\n) en fin ; on envoie la chaîne complète
        logger.debug("FY6900 TX: %r", cmd)
        self._conn.write(cmd.encode("utf-8"))
        # Documentation : le FY6900 renvoie 0x0a après exécution ; on lit cette réponse avant la commande suivante
        try:
            ack = self._conn.readline()
            if ack:
                logger.debug("FY6900 RX (ack): %r", ack)
        except Exception as e:
            logger.warning("FY6900 lecture ack après envoi: %s", e)

    def set_waveform(self, waveform: int, channel: int = 1) -> None:
        """Forme d'onde (0 = sinusoïde). channel 1 = WMW, channel 2 = WFW."""
        if channel == 2:
            self._send(FY.format_wfw(waveform))
        else:
            self._send(FY.format_wmw(waveform))

    def set_frequency_hz(self, freq_hz: float, channel: int = 1) -> None:
        """Fréquence en Hz (convertie en µHz, 14 chiffres, pour WMF/WFF). channel 1 = WMF, channel 2 = WFF."""
        if channel == 2:
            self._send(FY.format_wff_hz(freq_hz))
        else:
            self._send(FY.format_wmf_hz(freq_hz))

    def set_amplitude_peak_v(self, amplitude_v_peak: float, channel: int = 1) -> None:
        """Amplitude crête en V. channel 1 = WMA, channel 2 = WFA."""
        if channel == 2:
            self._send(FY.format_wfa(amplitude_v_peak))
        else:
            self._send(FY.format_wma(amplitude_v_peak))

    def set_offset_v(self, offset_v: float, channel: int = 1) -> None:
        """Offset en V. channel 1 = WMO, channel 2 = WFO."""
        if channel == 2:
            self._send(FY.format_wfo(offset_v))
        else:
            self._send(FY.format_wmo(offset_v))

    def set_output(self, on: bool, channel: int = 1) -> None:
        """Sortie ON (True) ou OFF (False). channel 1 = WMN, channel 2 = WFN."""
        if channel == 2:
            self._send(FY.format_wfn(on))
        else:
            self._send(FY.format_wmn(on))

    def set_duty_cycle_percent(self, duty_percent: float, channel: int = 1) -> None:
        """Rapport cyclique en % (0–100). channel 1 = WMD, channel 2 = WFD."""
        if channel == 2:
            self._send(FY.format_wfd(duty_percent))
        else:
            self._send(FY.format_wmd(duty_percent))

    def set_phase_deg(self, phase_deg: float, channel: int = 1) -> None:
        """Phase en degrés (0–360). channel 1 = WMP, channel 2 = WFP."""
        if channel == 2:
            self._send(FY.format_wfp(phase_deg))
        else:
            self._send(FY.format_wmp(phase_deg))

    def apply_sinus_1v_rms(self, freq_hz: float, channel: int = 1) -> None:
        """
        Configure sinusoïde, 1 V RMS (1.414 V crête), offset 0, fréquence, sortie ON.
        Séquence type pour un point du banc filtre.
        """
        self.set_waveform(0, channel=channel)
        self.set_amplitude_peak_v(1.414, channel=channel)
        self.set_offset_v(0.0, channel=channel)
        self.set_frequency_hz(freq_hz, channel=channel)
        self.set_output(True, channel=channel)
