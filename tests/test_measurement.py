"""
Tests de core.measurement.Measurement (avec ScpiProtocol mocké).
"""
from unittest.mock import MagicMock

import pytest

from core.measurement import Measurement


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
