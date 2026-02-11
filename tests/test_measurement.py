"""
Tests de core.measurement.Measurement (avec ScpiProtocol mocké).
"""
from unittest.mock import MagicMock

import pytest

from core.measurement import Measurement, MODE_IDS, UNIT_BY_MODE, RANGES_BY_MODE


class TestMeasurement:
    def test_parse_float_valid(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        assert m.parse_float("1.234") == 1.234
        assert m.parse_float("  2.5  ") == 2.5
        assert m.parse_float("1,5") == 1.5  # virgule

    def test_parse_float_invalid_returns_none(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        assert m.parse_float("") is None
        assert m.parse_float("abc") is None
        assert m.parse_float(None) is None

    def test_read_value_calls_meas(self):
        scpi = MagicMock()
        scpi.meas = MagicMock(return_value="1.234E+00")
        m = Measurement(scpi)
        out = m.read_value()
        assert out == "1.234E+00"
        scpi.meas.assert_called_once()

    def test_set_voltage_ac_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_voltage_ac()
        scpi.set_volt_ac.assert_called_once()

    def test_set_voltage_dc_calls_conf_voltage_dc(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_voltage_dc()
        scpi.conf_voltage_dc.assert_called_once()
        assert m.get_current_mode() == "volt_dc"

    def test_set_current_dc_set_current_ac_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_current_dc()
        scpi.conf_current_dc.assert_called_once()
        m.set_current_ac()
        scpi.conf_current_ac.assert_called_once()

    def test_set_resistance_set_resistance_4w_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_resistance()
        scpi.conf_res.assert_called_once()
        m.set_resistance_4w()
        scpi.conf_fres.assert_called_once()

    def test_set_frequency_set_period_set_capacitance_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_frequency()
        scpi.conf_freq.assert_called_once()
        m.set_period()
        scpi.conf_per.assert_called_once()
        m.set_capacitance()
        scpi.conf_cap.assert_called_once()

    def test_set_temperature_rtd_set_diode_set_continuity_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_temperature_rtd()
        scpi.conf_temp_rtd.assert_called_once()
        m.set_diode()
        scpi.conf_diod.assert_called_once()
        m.set_continuity()
        scpi.conf_cont.assert_called_once()

    def test_set_auto_range_false_does_not_call_auto(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_auto_range(False)
        scpi.auto.assert_not_called()

    def test_set_math_db_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_math_db(8.0)
        scpi.calc_func_db.assert_called_once()
        scpi.calc_db_ref.assert_called_once_with(8.0)

    def test_set_math_dbm_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_math_dbm(50.0)
        scpi.calc_func_dbm.assert_called_once()
        scpi.calc_dbm_ref.assert_called_once_with(50.0)

    def test_set_math_average_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_math_average()
        scpi.calc_func_average.assert_called_once()

    def test_read_secondary_value_calls_meas2(self):
        scpi = MagicMock()
        scpi.meas2 = MagicMock(return_value="1000.5")
        m = Measurement(scpi)
        out = m.read_secondary_value()
        assert out == "1000.5"
        scpi.meas2.assert_called_once()

    def test_reset_stats_calls_ask_calc_aver_all(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.reset_stats()
        scpi.ask_calc_aver_all.assert_called_once()

    def test_reset_stats_handles_exception(self):
        scpi = MagicMock()
        scpi.ask_calc_aver_all = MagicMock(side_effect=RuntimeError("comm error"))
        m = Measurement(scpi)
        m.reset_stats()
        scpi.ask_calc_aver_all.assert_called_once()

    def test_get_stats_handles_exception_returns_partial(self):
        scpi = MagicMock()
        scpi.ask_minimum = MagicMock(side_effect=RuntimeError())
        scpi.ask_maximum = MagicMock(return_value="2.0")
        scpi.ask_average = MagicMock(return_value="1.5")
        m = Measurement(scpi)
        s = m.get_stats()
        assert s["min"] is None
        assert s["max"] == 2.0
        assert s["avg"] == 1.5

    def test_get_stats_handles_exception_on_maximum(self):
        scpi = MagicMock()
        scpi.ask_minimum = MagicMock(return_value="1.0")
        scpi.ask_maximum = MagicMock(side_effect=RuntimeError())
        scpi.ask_average = MagicMock(return_value="1.5")
        m = Measurement(scpi)
        s = m.get_stats()
        assert s["min"] == 1.0
        assert s["max"] is None
        assert s["avg"] == 1.5

    def test_get_stats_handles_exception_on_average(self):
        scpi = MagicMock()
        scpi.ask_minimum = MagicMock(return_value="1.0")
        scpi.ask_maximum = MagicMock(return_value="2.0")
        scpi.ask_average = MagicMock(side_effect=RuntimeError())
        m = Measurement(scpi)
        s = m.get_stats()
        assert s["min"] == 1.0
        assert s["max"] == 2.0
        assert s["avg"] is None

    def test_set_rtd_type_pt100_calls_pt100(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_rtd_type("PT100")
        scpi.temp_rtd_type_pt100.assert_called_once()

    def test_set_rtd_type_other_calls_kits90(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_rtd_type("KITS90")
        scpi.temp_rtd_type_kits90.assert_called_once()
        m.set_rtd_type("")
        assert scpi.temp_rtd_type_kits90.call_count == 2

    def test_set_rtd_unit_f_k_c(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_rtd_unit("F")
        scpi.temp_rtd_unit_f.assert_called_once()
        m.set_rtd_unit("K")
        scpi.temp_rtd_unit_k.assert_called_once()
        m.set_rtd_unit("C")
        scpi.temp_rtd_unit_c.assert_called()

    def test_set_rtd_show_meas_all_temp(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_rtd_show("MEAS")
        scpi.temp_rtd_show_meas.assert_called_once()
        m.set_rtd_show("ALL")
        scpi.temp_rtd_show_all.assert_called_once()
        m.set_rtd_show("TEMP")
        scpi.temp_rtd_show_temp.assert_called()

    def test_set_continuity_threshold_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_continuity_threshold(5.0)
        scpi.cont_thre.assert_called_once_with(5.0)

    def test_reset_calls_scpi_rst(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.reset()
        scpi.rst.assert_called_once()

    def test_get_unit_for_current_mode(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        assert m.get_unit_for_current_mode() == "V"
        m.set_voltage_dc()
        assert m.get_unit_for_current_mode() == "V"
        m.set_frequency()
        assert m.get_unit_for_current_mode() == "Hz"
        m.set_resistance()
        assert m.get_unit_for_current_mode() == "Ω"

    def test_get_ranges_for_current_mode(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        ranges = m.get_ranges_for_current_mode()
        assert len(ranges) > 0
        assert ranges[0][0] == "500 mV"
        m.set_resistance()
        ranges = m.get_ranges_for_current_mode()
        assert any("kΩ" in r[0] or "Ω" in r[0] for r in ranges)

    def test_set_rate_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_rate("F")
        scpi.rate_f.assert_called_once()
        m.set_rate("M")
        scpi.rate_m.assert_called_once()
        m.set_rate("L")
        scpi.rate_l.assert_called_once()

    def test_set_auto_range_calls_auto(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_auto_range(True)
        scpi.auto.assert_called_once()

    def test_set_range_calls_set_range_value(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_range(5)
        scpi.set_range_value.assert_called_once_with(5)


    def test_set_secondary_display_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_secondary_display(True)
        scpi.func2_freq.assert_called_once()
        m.set_secondary_display(False)
        scpi.func2_none.assert_called_once()

    def test_set_math_off_calls_calc_stat_off(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_math_off()
        scpi.calc_stat_off.assert_called_once()

    def test_set_math_rel_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_math_rel(0.5)
        scpi.calc_func_null.assert_called_once()
        scpi.calc_null_offs.assert_called_once_with(0.5)

    def test_get_stats_returns_dict(self):
        scpi = MagicMock()
        scpi.ask_minimum = MagicMock(return_value="1.0")
        scpi.ask_maximum = MagicMock(return_value="2.0")
        scpi.ask_average = MagicMock(return_value="1.5")
        m = Measurement(scpi)
        s = m.get_stats()
        assert "min" in s and "max" in s and "avg" in s
        assert s["min"] == 1.0
        assert s["max"] == 2.0
        assert s["avg"] == 1.5

    def test_set_buzzer_calls_scpi(self):
        scpi = MagicMock()
        m = Measurement(scpi)
        m.set_buzzer(True)
        scpi.beep_on.assert_called_once()
        m.set_buzzer(False)
        scpi.beep_off.assert_called_once()


class TestMeasurementConstants:
    def test_mode_ids_count(self):
        assert len(MODE_IDS) == 12

    def test_unit_by_mode_cover_all_modes(self):
        for mode in MODE_IDS:
            assert mode in UNIT_BY_MODE
