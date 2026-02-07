"""
Logique mesures OWON : mode, plage, MEAS?.
Utilise ScpiProtocol ; appelé par meter_view et filter_test.
"""

from .scpi_protocol import ScpiProtocol

# Ordre des modes (aligné sur l'UI : V⎓, V~, A⎓, A~, Ω, Ω 4W, Hz, s, F, °C, ⊿, ⚡)
MODE_IDS = (
    "volt_dc", "volt_ac", "curr_dc", "curr_ac",
    "res", "fres", "freq", "per", "cap", "temp_rtd", "diod", "cont",
)

UNIT_BY_MODE = {
    "volt_dc": "V", "volt_ac": "V", "curr_dc": "A", "curr_ac": "A",
    "res": "Ω", "fres": "Ω", "freq": "Hz", "per": "s", "cap": "F",
    "temp_rtd": "°C", "diod": "V", "cont": "Ω",
}

# Plages par mode : liste de (libellé affiché, valeur SCPI)
RANGES_BY_MODE = {
    "volt_dc": [("500 mV", 0.5), ("5 V", 5), ("50 V", 50), ("500 V", 500), ("1000 V", 1000)],
    "volt_ac": [("500 mV", 0.5), ("5 V", 5), ("50 V", 50), ("500 V", 500), ("750 V", 750)],
    "curr_dc": [("50 mV", 0.05), ("500 mV", 0.5), ("5 V", 5), ("50 V", 50), ("500 V", 500), ("1000 V", 1000)],
    "curr_ac": [("50 mV", 0.05), ("500 mV", 0.5), ("5 V", 5), ("50 V", 50), ("500 V", 500), ("1000 V", 1000)],
    "res": [("500 Ω", 500), ("5 kΩ", 5e3), ("50 kΩ", 50e3), ("500 kΩ", 500e3), ("5 MΩ", 5e6), ("50 MΩ", 50e6), ("500 MΩ", 500e6)],
    "fres": [("500 Ω", 500), ("5 kΩ", 5e3), ("50 kΩ", 50e3)],
    "freq": [],   # pas de plage manuelle typique
    "per": [],
    "cap": [("50 nF", 50e-9), ("500 nF", 500e-9), ("5 µF", 5e-6), ("50 µF", 50e-6), ("500 µF", 500e-6), ("5 mF", 5e-3), ("50 mF", 50e-3)],
    "temp_rtd": [("KITS90", "KITS90"), ("PT100", "PT100")],
    "diod": [],
    "cont": [],
}


class Measurement:
    """Couche mesure : configure le mode (ex. tension AC) et récupère la valeur."""

    def __init__(self, scpi: ScpiProtocol):
        self._scpi = scpi
        self._current_mode = "volt_dc"

    def set_voltage_dc(self) -> None:
        self._scpi.conf_voltage_dc()
        self._current_mode = "volt_dc"
    def set_voltage_ac(self) -> None:
        """Passe en mode tension AC (pour banc filtre : mesure Us RMS)."""
        self._scpi.set_volt_ac()
        self._current_mode = "volt_ac"
    def set_current_dc(self) -> None:
        self._scpi.conf_current_dc()
        self._current_mode = "curr_dc"
    def set_current_ac(self) -> None:
        self._scpi.conf_current_ac()
        self._current_mode = "curr_ac"
    def set_resistance(self) -> None:
        self._scpi.conf_res()
        self._current_mode = "res"
    def set_resistance_4w(self) -> None:
        self._scpi.conf_fres()
        self._current_mode = "fres"
    def set_frequency(self) -> None:
        self._scpi.conf_freq()
        self._current_mode = "freq"
    def set_period(self) -> None:
        self._scpi.conf_per()
        self._current_mode = "per"
    def set_capacitance(self) -> None:
        self._scpi.conf_cap()
        self._current_mode = "cap"
    def set_temperature_rtd(self) -> None:
        self._scpi.conf_temp_rtd()
        self._current_mode = "temp_rtd"
    def set_diode(self) -> None:
        self._scpi.conf_diod()
        self._current_mode = "diod"
    def set_continuity(self) -> None:
        self._scpi.conf_cont()
        self._current_mode = "cont"

    def set_auto_range(self, on: bool) -> None:
        if on:
            self._scpi.auto()

    def set_range(self, value) -> None:
        """Plage manuelle (valeur SCPI : float ou str pour RTD)."""
        self._scpi.set_range_value(value)

    def set_rate(self, rate: str) -> None:
        """rate: 'F' | 'M' | 'L' (Rapide | Moyenne | Lente)."""
        if rate == "F":
            self._scpi.rate_f()
        elif rate == "M":
            self._scpi.rate_m()
        elif rate == "L":
            self._scpi.rate_l()

    def get_current_mode(self) -> str:
        return self._current_mode

    def get_unit_for_current_mode(self) -> str:
        return UNIT_BY_MODE.get(self._current_mode, "V")

    def get_ranges_for_current_mode(self):
        """Liste de (libellé, valeur SCPI) pour le mode actuel."""
        return list(RANGES_BY_MODE.get(self._current_mode, []))

    # Affichage secondaire (Hz)
    def set_secondary_display(self, show_hz: bool) -> None:
        if show_hz:
            self._scpi.func2_freq()
        else:
            self._scpi.func2_none()

    def read_secondary_value(self) -> str:
        """Valeur affichage secondaire (MEAS2?)."""
        return self._scpi.meas2()

    # Fonctions math (CALCulate)
    def set_math_off(self) -> None:
        self._scpi.calc_stat_off()

    def set_math_rel(self, offset: float) -> None:
        self._scpi.calc_func_null()
        self._scpi.calc_null_offs(offset)

    def set_math_db(self, ref_ohm: float) -> None:
        self._scpi.calc_func_db()
        self._scpi.calc_db_ref(ref_ohm)

    def set_math_dbm(self, ref_ohm: float) -> None:
        self._scpi.calc_func_dbm()
        self._scpi.calc_dbm_ref(ref_ohm)

    def set_math_average(self) -> None:
        self._scpi.calc_func_average()

    def get_stats(self) -> dict:
        """Min, max, moyenne (et éventuellement N) en mode Moyenne. Retourne dict avec clés min, max, avg, n."""
        out = {"min": None, "max": None, "avg": None, "n": None}
        try:
            s = self._scpi.ask_minimum()
            out["min"] = self.parse_float(s)
        except Exception:
            pass
        try:
            s = self._scpi.ask_maximum()
            out["max"] = self.parse_float(s)
        except Exception:
            pass
        try:
            s = self._scpi.ask_average()
            out["avg"] = self.parse_float(s)
        except Exception:
            pass
        return out

    def reset_stats(self) -> None:
        """Réinitialise les statistiques (mode Moyenne)."""
        try:
            self._scpi.ask_calc_aver_all()
        except Exception:
            pass

    # Paramètres avancés : température RTD
    def set_rtd_type(self, rtd_type: str) -> None:
        if (rtd_type or "").upper() == "PT100":
            self._scpi.temp_rtd_type_pt100()
        else:
            self._scpi.temp_rtd_type_kits90()

    def set_rtd_unit(self, unit: str) -> None:
        u = (unit or "C").upper()[:1]
        if u == "F":
            self._scpi.temp_rtd_unit_f()
        elif u == "K":
            self._scpi.temp_rtd_unit_k()
        else:
            self._scpi.temp_rtd_unit_c()

    def set_rtd_show(self, show: str) -> None:
        s = (show or "TEMP").upper()
        if "MEAS" in s:
            self._scpi.temp_rtd_show_meas()
        elif "ALL" in s:
            self._scpi.temp_rtd_show_all()
        else:
            self._scpi.temp_rtd_show_temp()

    # Continuité
    def set_continuity_threshold(self, ohm: float) -> None:
        self._scpi.cont_thre(ohm)

    # Buzzer
    def set_buzzer(self, on: bool) -> None:
        if on:
            self._scpi.beep_on()
        else:
            self._scpi.beep_off()

    def read_value(self) -> str:
        """Lance une mesure et retourne la chaîne brute (ex. '1.234E+00')."""
        return self._scpi.meas()

    def parse_float(self, value_str: str):  # -> Optional[float]
        """Parse la réponse MEAS? en float (V). Retourne None si invalide."""
        if value_str is None:
            return None
        try:
            return float(value_str.strip().replace(",", "."))
        except (ValueError, TypeError):
            return None

    def reset(self) -> None:
        """Réinitialisation multimètre (*RST)."""
        self._scpi.rst()
        self._current_mode = "volt_dc"
