"""
Stub Fy6900Protocol pour la maquette.
"""

class Fy6900Protocol:
    def __init__(self, connection):
        self._conn = connection

    def set_frequency_hz(self, channel: int, hz: float) -> None:
        pass

    def set_amplitude_v_peak(self, channel: int, v: float) -> None:
        pass

    def set_output(self, channel: int, on: bool) -> None:
        pass

    def write(self, cmd: bytes) -> None:
        pass
