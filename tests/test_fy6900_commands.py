"""
Tests du module core.fy6900_commands : format des commandes FY6900.
"""
import pytest

from core import fy6900_commands as FY


class TestFormatWmw:
    def test_sinus(self):
        assert FY.format_wmw(0) == "WMW0\n"

    def test_other_waveform(self):
        assert FY.format_wmw(1) == "WMW1\n"


class TestFormatWmfHz:
    def test_100_hz(self):
        assert FY.format_wmf_hz(100) == "WMF100.000000\n"

    def test_1000_hz(self):
        assert FY.format_wmf_hz(1000) == "WMF1000.000000\n"

    def test_freq_6_decimals(self):
        assert FY.format_wmf_hz(12345678.901234) == "WMF12345678.901234\n"

    def test_clamp_negative(self):
        assert FY.format_wmf_hz(-1) == "WMF0.000000\n"

    def test_fractional_hz(self):
        assert FY.format_wmf_hz(1.5) == "WMF1.500000\n"


class TestFormatWma:
    def test_amplitude(self):
        assert FY.format_wma(1.41) == "WMA1.41\n"
        assert FY.format_wma(5.0) == "WMA5.00\n"


class TestFormatWmo:
    def test_offset_zero(self):
        assert FY.format_wmo(0) == "WMO0.00\n"


class TestFormatWmn:
    def test_on(self):
        assert FY.format_wmn(True) == "WMN1\n"

    def test_off(self):
        assert FY.format_wmn(False) == "WMN0\n"
