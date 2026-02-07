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
