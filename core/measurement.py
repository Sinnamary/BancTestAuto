"""
Logique mesures OWON : mode, plage, MEAS?.
Utilise ScpiProtocol ; appelé par meter_view et filter_test.
"""
from .scpi_protocol import ScpiProtocol


class Measurement:
    """Couche mesure : configure le mode (ex. tension AC) et récupère la valeur."""

    def __init__(self, scpi: ScpiProtocol):
        self._scpi = scpi

    def set_voltage_ac(self) -> None:
        """Passe en mode tension AC (pour banc filtre : mesure Us RMS)."""
        self._scpi.set_volt_ac()

    def read_value(self) -> str:
        """Lance une mesure et retourne la chaîne brute (ex. '1.234E+00')."""
        return self._scpi.meas()

    def parse_float(self, value_str: str) -> float | None:
        """Parse la réponse MEAS? en float (V). Retourne None si invalide."""
        try:
            return float(value_str.strip().replace(",", "."))
        except (ValueError, TypeError):
            return None
