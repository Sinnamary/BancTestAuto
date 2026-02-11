"""
Stub ScpiProtocol pour la maquette.
"""

class ScpiProtocol:
    def __init__(self, connection):
        self._conn = connection

    def write(self, cmd: str) -> None:
        pass

    def ask(self, cmd: str) -> str:
        return ""

    def conf_voltage_dc(self) -> None:
        pass

    def set_volt_ac(self) -> None:
        pass
