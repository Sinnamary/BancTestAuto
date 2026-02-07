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
