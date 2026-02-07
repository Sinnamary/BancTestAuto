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
        # 100 Hz = 100_000_000 µHz (14 chiffres)
        expected = f"WMF{100_000_000:014d}\n"
        assert FY.format_wmf_hz(100) == expected

    def test_1000_hz(self):
        assert "WMF" in FY.format_wmf_hz(1000)
        assert FY.format_wmf_hz(1000).strip().endswith("01000000000")

    def test_clamp_negative(self):
        out = FY.format_wmf_hz(-1)
        assert out.startswith("WMF")
        assert "00000000000000" in out

    def test_clamp_high(self):
        out = FY.format_wmf_hz(1e15)
        assert out.startswith("WMF")
        assert "99999999999999" in out


class TestFormatWma:
    def test_amplitude(self):
        assert FY.format_wma(1.414) == "WMA1.414\n"


class TestFormatWmo:
    def test_offset_zero(self):
        assert FY.format_wmo(0) == "WMO0.00\n"


class TestFormatWmn:
    def test_on(self):
        assert FY.format_wmn(True) == "WMN1\n"

    def test_off(self):
        assert FY.format_wmn(False) == "WMN0\n"
