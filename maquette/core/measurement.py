"""
Stub Measurement pour la maquette. MODE_IDS pour l'UI multimètre.
"""

MODE_IDS = (
    "volt_dc", "volt_ac", "curr_dc", "curr_ac",
    "res", "fres", "freq", "per", "cap", "temp_rtd", "diod", "cont",
)

UNIT_BY_MODE = {
    "volt_dc": "V", "volt_ac": "V", "curr_dc": "A", "curr_ac": "A",
    "res": "Ω", "fres": "Ω", "freq": "Hz", "per": "s", "cap": "F",
    "temp_rtd": "°C", "diod": "V", "cont": "Ω",
}

RANGES_BY_MODE = {m: [] for m in MODE_IDS}


class Measurement:
    def __init__(self, scpi):
        self._scpi = scpi
        self._current_mode = "volt_dc"

    def set_voltage_dc(self) -> None:
        pass

    def set_voltage_ac(self) -> None:
        pass

    def measure(self) -> tuple[float, str]:
        return 0.0, "V"

    def get_current_mode(self) -> str:
        return self._current_mode
