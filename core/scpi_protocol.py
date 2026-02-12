"""
Protocole SCPI : envoi/réception sur une SerialConnection.
Utilisé par Measurement et toute commande OWON.
"""
from .serial_connection import SerialConnection
from . import scpi_commands as SCPI
from .app_logger import get_logger

logger = get_logger(__name__)


class ScpiProtocol:
    """Envoi de commandes SCPI et lecture des réponses (utilise SerialConnection)."""

    def __init__(self, connection: SerialConnection):
        self._conn = connection

    def write(self, command: str) -> None:
        """Envoie une commande SCPI (sans retour à la ligne si déjà présent)."""
        cmd = command.strip()
        if not cmd.endswith("\n"):
            cmd += "\n"
        logger.debug("SCPI TX: %s", cmd.rstrip())
        self._conn.write(cmd.encode("utf-8"))

    def ask(self, command: str) -> str:
        """Envoie une commande et retourne la réponse (jusqu'à LF)."""
        self.write(command)
        line = self._conn.readline()
        reply = line.decode("utf-8", errors="replace").strip()
        logger.debug("SCPI RX: %r", reply)
        return reply

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

    def conf_voltage_dc(self) -> None:
        self.write(SCPI.CONF_VOLT_DC)
    def conf_voltage_ac(self) -> None:
        self.write(SCPI.CONF_VOLT_AC)
    def conf_current_dc(self) -> None:
        self.write(SCPI.CONF_CURR_DC)
    def conf_current_ac(self) -> None:
        self.write(SCPI.CONF_CURR_AC)
    def conf_res(self) -> None:
        self.write(SCPI.CONF_RES)
    def conf_fres(self) -> None:
        self.write(SCPI.CONF_FRES)
    def conf_freq(self) -> None:
        self.write(SCPI.CONF_FREQ)
    def conf_per(self) -> None:
        self.write(SCPI.CONF_PER)
    def conf_cap(self) -> None:
        self.write(SCPI.CONF_CAP)
    def conf_temp_rtd(self) -> None:
        self.write(SCPI.CONF_TEMP_RTD)
    def conf_diod(self) -> None:
        self.write(SCPI.CONF_DIOD)
    def conf_cont(self) -> None:
        self.write(SCPI.CONF_CONT)

    def auto(self) -> None:
        """Plage automatique."""
        self.write(SCPI.AUTO)

    def set_range_value(self, value) -> None:
        """Plage manuelle (valeur SCPI : 5, 500E-3, 5E3, etc.)."""
        self.write(SCPI.RANGE_VALUE(value))

    def rate_f(self) -> None:
        self.write(SCPI.RATE_F)
    def rate_m(self) -> None:
        self.write(SCPI.RATE_M)
    def rate_l(self) -> None:
        self.write(SCPI.RATE_L)

    def rst(self) -> None:
        """Réinitialisation appareil (*RST)."""
        self.write(SCPI.RST)

    def meas2(self) -> str:
        """Mesure affichage secondaire (MEAS2?)."""
        return self.ask(SCPI.MEAS2)

    def func2_freq(self) -> None:
        """Active l'affichage secondaire (fréquence Hz)."""
        self.write(SCPI.FUNC2_FREQ)

    def func2_none(self) -> None:
        """Désactive l'affichage secondaire."""
        self.write(SCPI.FUNC2_NONE)

    # CALCulate (math)
    def calc_stat_off(self) -> None:
        self.write(SCPI.CALC_STAT_OFF)

    def calc_func_null(self) -> None:
        self.write(SCPI.CALC_FUNC_NULL)

    def calc_null_offs(self, value: float) -> None:
        self.write(SCPI.CALC_NULL_OFFS(value))

    def calc_func_db(self) -> None:
        self.write(SCPI.CALC_FUNC_DB)

    def calc_db_ref(self, ohm: float) -> None:
        self.write(SCPI.CALC_DB_REF(ohm))

    def calc_func_dbm(self) -> None:
        self.write(SCPI.CALC_FUNC_DBM)

    def calc_dbm_ref(self, ohm: float) -> None:
        self.write(SCPI.CALC_DBM_REF(ohm))

    def calc_func_average(self) -> None:
        self.write(SCPI.CALC_FUNC_AVERAGE)

    def ask_calc_aver_all(self) -> str:
        """CALC:AVER:ALL? (réinitialise et retourne stats)."""
        return self.ask(SCPI.CALC_AVER_ALL_QUERY)

    def ask_average(self) -> str:
        return self.ask(SCPI.AVERAGE_QUERY)

    def ask_maximum(self) -> str:
        return self.ask(SCPI.MAXIMUM_QUERY)

    def ask_minimum(self) -> str:
        return self.ask(SCPI.MINIMUM_QUERY)

    # Température RTD
    def temp_rtd_type_kits90(self) -> None:
        self.write(SCPI.TEMP_RTD_TYPE_KITS90)

    def temp_rtd_type_pt100(self) -> None:
        self.write(SCPI.TEMP_RTD_TYPE_PT100)

    def temp_rtd_unit_c(self) -> None:
        self.write(SCPI.TEMP_RTD_UNIT_C)

    def temp_rtd_unit_f(self) -> None:
        self.write(SCPI.TEMP_RTD_UNIT_F)

    def temp_rtd_unit_k(self) -> None:
        self.write(SCPI.TEMP_RTD_UNIT_K)

    def temp_rtd_show_temp(self) -> None:
        self.write(SCPI.TEMP_RTD_SHOW_TEMP)

    def temp_rtd_show_meas(self) -> None:
        self.write(SCPI.TEMP_RTD_SHOW_MEAS)

    def temp_rtd_show_all(self) -> None:
        self.write(SCPI.TEMP_RTD_SHOW_ALL)

    # Continuité
    def cont_thre(self, value: float) -> None:
        self.write(SCPI.CONT_THRE(value))

    # Buzzer
    def beep_on(self) -> None:
        self.write(SCPI.SYST_BEEP_ON)

    def beep_off(self) -> None:
        self.write(SCPI.SYST_BEEP_OFF)
