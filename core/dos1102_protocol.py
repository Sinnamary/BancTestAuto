"""
Protocole SCPI pour l'oscilloscope HANMATEK DOS1102.
Envoi/réception sur une SerialConnection (USB virtuelle série).
"""
from .serial_connection import SerialConnection
from . import dos1102_commands as CMD
from .app_logger import get_logger

logger = get_logger(__name__)


class Dos1102Protocol:
    """Envoi de commandes SCPI et lecture des réponses pour le DOS1102."""

    def __init__(self, connection: SerialConnection):
        self._conn = connection

    def write(self, command: str) -> None:
        """Envoie une commande SCPI (termine par \\n si absent)."""
        cmd = command.strip()
        if not cmd.endswith("\n"):
            cmd += "\n"
        logger.debug("DOS1102 TX: %s", cmd.rstrip())
        self._conn.write(cmd.encode("utf-8"))

    def ask(self, command: str) -> str:
        """Envoie une commande et retourne la réponse (jusqu'à LF)."""
        self.write(command)
        line = self._conn.readline()
        reply = line.decode("utf-8", errors="replace").strip()
        logger.debug("DOS1102 RX: %r", reply)
        return reply

    def idn(self) -> str:
        """Identification (*IDN?)."""
        return self.ask(CMD.IDN)

    def rst(self) -> None:
        """Réinitialisation (*RST)."""
        self.write(CMD.RST)

    # Acquisition
    def set_acq_samp(self) -> None:
        self.write(CMD.ACQ_MODE_SAMP)

    def set_acq_peak(self) -> None:
        self.write(CMD.ACQ_MODE_PEAK)

    def set_acq_ave(self) -> None:
        self.write(CMD.ACQ_MODE_AVE)

    # Couplage
    def set_ch1_coupling(self, mode: str) -> None:
        """mode: DC, AC, GND."""
        self.write(CMD.CH_COUP(1, mode))

    def set_ch2_coupling(self, mode: str) -> None:
        self.write(CMD.CH_COUP(2, mode))

    # Échelle / position / offset
    def set_ch_scale(self, ch: int, value) -> None:
        self.write(CMD.CH_SCA(ch, value))

    def set_ch_pos(self, ch: int, value) -> None:
        self.write(CMD.CH_POS(ch, value))

    def set_ch_offset(self, ch: int, value) -> None:
        self.write(CMD.CH_OFFS(ch, value))

    # Sonde
    def set_ch_probe(self, ch: int, value: str) -> None:
        """value: 1X, 10X, 100X, 1000X."""
        self.write(CMD.CH_PROBE(ch, value))

    # Inversion
    def set_ch_inv(self, ch: int, on: bool) -> None:
        self.write(CMD.CH_INV(ch, "ON" if on else "OFF"))

    # Base de temps
    def set_hor_offset(self, value) -> None:
        self.write(CMD.HOR_OFFS(value))

    def set_hor_scale(self, value) -> None:
        self.write(CMD.HOR_SCAL(value))

    # Trigger
    def set_trig_edge(self) -> None:
        self.write(CMD.TRIG_EDGE)

    def set_trig_video(self) -> None:
        self.write(CMD.TRIG_VIDEO)

    def set_trig_type_single(self) -> None:
        self.write(CMD.TRIG_TYPE_SING)

    def set_trig_type_alt(self) -> None:
        self.write(CMD.TRIG_TYPE_ALT)

    # Mesures
    def meas(self) -> str:
        """Requête mesure générale (:MEAS?)."""
        return self.ask(CMD.MEAS_QUERY)

    def meas_ch(self, ch: int, meas_type: str) -> str:
        """Ex. meas_ch(1, 'FREQuency') -> :MEAS:CH1:FREQuency?"""
        return self.ask(CMD.MEAS_CH_QUERY(ch, meas_type))
