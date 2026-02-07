"""
Protocole FY6900 (FeelTech) : WMW, WMF, WMA, WMO, WMN.
Utilise SerialConnection ; appelé par generator_view et filter_test.
"""
from .serial_connection import SerialConnection
from . import fy6900_commands as FY


class Fy6900Protocol:
    """
    Commandes FY6900 sur une liaison série.
    Débit 115200, fin de commande 0x0a (LF).
    """

    def __init__(self, connection: SerialConnection):
        self._conn = connection

    def _send(self, cmd: str) -> None:
        self._conn.write(cmd.encode("utf-8"))

    def set_waveform(self, waveform: int) -> None:
        """WMW : forme d'onde (0 = sinusoïde)."""
        self._send(FY.format_wmw(waveform))

    def set_frequency_hz(self, freq_hz: float) -> None:
        """WMF : fréquence en Hz (converti en µHz sur 14 chiffres)."""
        self._send(FY.format_wmf_hz(freq_hz))

    def set_amplitude_peak_v(self, amplitude_v_peak: float) -> None:
        """WMA : amplitude crête en V (ex. 1.414 pour 1 V RMS)."""
        self._send(FY.format_wma(amplitude_v_peak))

    def set_offset_v(self, offset_v: float) -> None:
        """WMO : offset en V."""
        self._send(FY.format_wmo(offset_v))

    def set_output(self, on: bool) -> None:
        """WMN : sortie ON (True) ou OFF (False)."""
        self._send(FY.format_wmn(on))

    def apply_sinus_1v_rms(self, freq_hz: float) -> None:
        """
        Configure sinusoïde, 1 V RMS (WMA 1.414), offset 0, fréquence, sortie ON.
        Séquence type pour un point du banc filtre.
        """
        self.set_waveform(0)
        self.set_amplitude_peak_v(1.414)
        self.set_offset_v(0.0)
        self.set_frequency_hz(freq_hz)
        self.set_output(True)
