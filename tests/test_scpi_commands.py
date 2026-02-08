"""
Tests du module core.scpi_commands : constantes SCPI (présence et cohérence).
"""
from core import scpi_commands as SCPI


class TestScpiConstants:
    def test_idn(self):
        assert SCPI.IDN == "*IDN?"

    def test_meas(self):
        assert "MEAS" in SCPI.MEAS

    def test_conf_volt_ac(self):
        assert "VOLT" in SCPI.CONF_VOLT_AC
        assert "AC" in SCPI.CONF_VOLT_AC

    def test_conf_volt_ac_meas_tuple(self):
        assert SCPI.CONF_VOLT_AC_MEAS == (SCPI.CONF_VOLT_AC, SCPI.MEAS)

    def test_rate_constants(self):
        assert SCPI.RATE_F == "RATE F"
        assert SCPI.RATE_M == "RATE M"
        assert SCPI.RATE_L == "RATE L"

    def test_range_value(self):
        assert "RANGE" in SCPI.RANGE_VALUE(5)
        assert "5" in SCPI.RANGE_VALUE(5)
        assert "500E-3" in SCPI.RANGE_VALUE(0.5) or "0.5" in SCPI.RANGE_VALUE(0.5)

    def test_calc_constants(self):
        assert "CALC" in SCPI.CALC_STAT_OFF
        assert "OFF" in SCPI.CALC_STAT_OFF
        assert "NULL" in SCPI.CALC_FUNC_NULL
        assert "AVERage" in SCPI.CALC_FUNC_AVERAGE

    def test_calc_null_offs(self):
        assert "CALC" in SCPI.CALC_NULL_OFFS(1.5)
        assert "1.5" in SCPI.CALC_NULL_OFFS(1.5)

    def test_calc_db_ref(self):
        assert "CALC" in SCPI.CALC_DB_REF(600)
        assert "600" in SCPI.CALC_DB_REF(600)

    def test_calc_dbm_ref(self):
        assert "CALC" in SCPI.CALC_DBM_REF(50)
        assert "50" in SCPI.CALC_DBM_REF(50)

    def test_cont_thre(self):
        assert "CONT" in SCPI.CONT_THRE(10)
        assert "10" in SCPI.CONT_THRE(10)
