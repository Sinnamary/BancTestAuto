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
        data = cmd.encode("utf-8")
        logger.debug("DOS1102 TX (%d octets): %r", len(data), cmd.rstrip())
        try:
            n = self._conn.write(data)
            logger.debug("DOS1102 TX écrit: %d octets", n)
        except Exception as e:
            logger.exception("DOS1102 TX erreur: %s", e)
            raise

    def ask(self, command: str) -> str:
        """Envoie une commande et retourne la réponse (jusqu'à LF)."""
        logger.debug("DOS1102 ask: envoi commande %r", command.strip())
        self.write(command)
        try:
            logger.debug("DOS1102 ask: lecture réponse (readline)...")
            line = self._conn.readline()
            logger.debug("DOS1102 ask: reçu %d octets bruts: %r", len(line), line[:200] if len(line) > 200 else line)
            reply = line.decode("utf-8", errors="replace").strip()
            # Retirer le prompt DOS1102 en fin de ligne (ex. "->" ou "   HANMA,...->")
            if reply.endswith("->"):
                reply = reply[:-2].strip()
            logger.debug("DOS1102 RX: %r", reply)
            if not reply and len(line) > 0:
                logger.debug("DOS1102 RX: réponse non vide mais strip() vide (caractères spéciaux?)")
            return reply
        except Exception as e:
            logger.exception("DOS1102 ask erreur (timeout?) : %s", e)
            raise

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

    def meas_all_per_channel(self, ch: int) -> dict[str, str]:
        """
        Requête toutes les mesures disponibles sur une voie (CH1 ou CH2).
        Retourne un dict { libellé: valeur } pour chaque type de MEAS_TYPES_PER_CHANNEL.
        Les mesures en erreur ou vides sont omises ou mises à '—'.
        """
        out: dict[str, str] = {}
        for label, meas_type in CMD.MEAS_TYPES_PER_CHANNEL:
            try:
                r = self.ask(CMD.MEAS_CH_QUERY(ch, meas_type))
                out[label] = r.strip() if r else "—"
            except Exception as e:
                logger.debug("meas_all_per_channel CH%d %s: %s", ch, meas_type, e)
                out[label] = f"Erreur: {e}"
        return out

    def meas_all_inter_channel(self) -> dict[str, str]:
        """
        Requête les mesures inter-canal (délai CH2 vs CH1).
        Utilise CH2 pour RISEPHASEDELAY, RDELay, FDELay.
        Utile pour diagramme de Bode phase : phase_deg = (délai / période) × 360.
        """
        out: dict[str, str] = {}
        for label, meas_type in CMD.MEAS_TYPES_INTER_CHANNEL:
            try:
                r = self.ask(CMD.MEAS_CH_QUERY(2, meas_type))
                out[label] = r.strip() if r else "—"
            except Exception as e:
                logger.debug("meas_all_inter_channel %s: %s", meas_type, e)
                out[label] = f"Erreur: {e}"
        return out

    def waveform_data_raw(
        self,
        timeout_override_sec: float | None = 5.0,
        use_long_command: bool = False,
    ) -> str | bytes:
        """
        Envoie :WAV:DATA:ALL? et lit la réponse (ASCII ou bloc SCPI #n...).
        Si la réponse commence par #, lit un bloc binaire SCPI (# + 1 chiffre + n chiffres = longueur + données).
        Sinon lit une ligne (réponse ASCII).
        timeout_override_sec : timeout plus long pour les grosses courbes (optionnel).
        use_long_command : si True, utilise la forme longue :WAVeform:DATA:ALL?.
        """
        # On envoie la commande sous forme de chaîne ; Dos1102Protocol.write
        # se charge d'ajouter le LF final et d'encoder en UTF‑8.
        cmd = CMD.WAVEFORM_DATA_ALL_LONG if use_long_command else CMD.WAVEFORM_DATA_ALL
        self.write(cmd)
        first = self._conn.read(1)
        if not first:
            return ""
        if first == b"#":
            # Format bloc SCPI : #n<ndigits> puis n chiffres donnant la longueur, puis les octets
            n_dig = self._conn.read(1)
            if not n_dig or not n_dig.isdigit():
                return first + (n_dig or b"")
            n = int(n_dig.decode())
            len_buf = self._conn.read(n)
            if len(len_buf) != n:
                return first + n_dig + len_buf
            try:
                length = int(len_buf.decode())
            except ValueError:
                return first + n_dig + len_buf
            data = self._conn.read(length)
            return data
        # Réponse ASCII (une ligne)
        rest = self._conn.readline()
        try:
            return (first + rest).decode("utf-8", errors="replace").strip()
        except Exception:
            return first + rest
