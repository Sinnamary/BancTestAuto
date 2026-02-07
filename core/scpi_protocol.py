"""
Protocole SCPI : envoi/réception sur une SerialConnection.
Utilisé par Measurement et toute commande OWON.
"""
from .serial_connection import SerialConnection
from . import scpi_commands as SCPI


class ScpiProtocol:
    """Envoi de commandes SCPI et lecture des réponses (utilise SerialConnection)."""

    def __init__(self, connection: SerialConnection):
        self._conn = connection

    def write(self, command: str) -> None:
        """Envoie une commande SCPI (sans retour à la ligne si déjà présent)."""
        cmd = command.strip()
        if not cmd.endswith("\n"):
            cmd += "\n"
        self._conn.write(cmd.encode("utf-8"))

    def ask(self, command: str) -> str:
        """Envoie une commande et retourne la réponse (jusqu'à LF)."""
        self.write(command)
        line = self._conn.readline()
        return line.decode("utf-8", errors="replace").strip()

    def idn(self) -> str:
        """Identification (*IDN?)."""
        return self.ask(SCPI.IDN)

    def meas(self) -> str:
        """Mesure (MEAS?)."""
        return self.ask(SCPI.MEAS)

    def meas1(self) -> str:
        """Mesure voie 1 (MEAS1?)."""
        return self.ask(SCPI.MEAS1)

    def set_volt_ac(self) -> None:
        """Mode tension AC (pour banc filtre)."""
        self.write(SCPI.CONF_VOLT_AC)
        self.write(SCPI.AUTO)
