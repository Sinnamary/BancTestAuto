"""
Tests de core.scpi_protocol.ScpiProtocol avec une SerialConnection mockée.
"""
from unittest.mock import MagicMock

import pytest

from core.scpi_protocol import ScpiProtocol


class TestScpiProtocol:
    def test_write_appends_newline_if_missing(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.write("CONF:VOLT:DC")
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0]
        assert arg.decode("utf-8").strip() == "CONF:VOLT:DC"
        assert arg.endswith(b"\n")

    def test_ask_sends_and_returns_decoded_line(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"1.234E+00\n")
        scpi = ScpiProtocol(conn)
        out = scpi.ask("*IDN?")
        assert out == "1.234E+00"
        assert conn.write.called
        assert conn.readline.called

    def test_idn_sends_idn_command(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"OWON,XDM2041,123\n")
        scpi = ScpiProtocol(conn)
        out = scpi.idn()
        assert "OWON" in out or "XDM" in out or "123" in out
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "*IDN?" in call_arg

    def test_set_volt_ac_writes_conf_and_auto(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.set_volt_ac()
        assert conn.write.call_count >= 2

    def test_rst_writes_rst_command(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.rst()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert "*RST" in arg

    def test_auto_writes_auto(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.auto()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert "AUTO" in arg

    def test_set_range_value_writes_range(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.set_range_value(5)
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert "RANGE" in arg
        assert "5" in arg

    def test_rate_f_writes_rate_f(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.rate_f()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert arg == "RATE F"

    def test_meas2_asks_meas2(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"123.45\n")
        scpi = ScpiProtocol(conn)
        out = scpi.meas2()
        assert out == "123.45"
        assert conn.write.called

    def test_func2_freq_writes_freq(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.func2_freq()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8")
        assert "FREQ" in arg

    def test_calc_stat_off_writes_calc(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.calc_stat_off()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8")
        assert "CALC" in arg

    def test_beep_off_writes_beep(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.beep_off()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8")
        assert "BEEP" in arg

    def test_conf_voltage_dc_writes_conf(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.conf_voltage_dc()
        conn.write.assert_called_once()
        assert "VOLT" in conn.write.call_args[0][0].decode("utf-8") and "DC" in conn.write.call_args[0][0].decode("utf-8")

    def test_conf_current_ac_writes_conf(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.conf_current_ac()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8")
        assert "CURR" in arg and "AC" in arg

    def test_conf_res_conf_fres_conf_freq_conf_per_conf_cap(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.conf_res()
        assert conn.write.called
        conn.write.reset_mock()
        scpi.conf_fres()
        scpi.conf_freq()
        scpi.conf_per()
        scpi.conf_cap()
        assert conn.write.call_count == 4

    def test_conf_temp_rtd_conf_diod_conf_cont(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.conf_temp_rtd()
        scpi.conf_diod()
        scpi.conf_cont()
        assert conn.write.call_count == 3

    def test_rate_m_rate_l(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.rate_m()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert "RATE" in arg and "M" in arg
        scpi.rate_l()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert "RATE" in arg and "L" in arg

    def test_meas1_asks_meas1(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"42.0\n")
        scpi = ScpiProtocol(conn)
        out = scpi.meas1()
        assert out == "42.0"

    def test_func2_none_writes(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.func2_none()
        conn.write.assert_called_once()

    def test_calc_null_offs_calc_db_ref_calc_dbm_ref(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.calc_func_null()
        scpi.calc_null_offs(0.5)
        scpi.calc_func_db()
        scpi.calc_db_ref(8.0)
        scpi.calc_func_dbm()
        scpi.calc_dbm_ref(50.0)
        scpi.calc_func_average()
        assert conn.write.call_count >= 6

    def test_ask_calc_aver_all_ask_average_ask_maximum_ask_minimum(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"1.5\n")
        scpi = ScpiProtocol(conn)
        assert scpi.ask_calc_aver_all() == "1.5"
        assert scpi.ask_average() == "1.5"
        assert scpi.ask_maximum() == "1.5"
        assert scpi.ask_minimum() == "1.5"

    def test_temp_rtd_type_and_unit_and_show(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.temp_rtd_type_kits90()
        scpi.temp_rtd_type_pt100()
        scpi.temp_rtd_unit_c()
        scpi.temp_rtd_unit_f()
        scpi.temp_rtd_unit_k()
        scpi.temp_rtd_show_temp()
        scpi.temp_rtd_show_meas()
        scpi.temp_rtd_show_all()
        assert conn.write.call_count >= 8

    def test_cont_thre_beep_on(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.cont_thre(10.0)
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8")
        assert "THRE" in arg or "10" in arg
        scpi.beep_on()
        arg = conn.write.call_args[0][0].decode("utf-8")
        assert "BEEP" in arg
