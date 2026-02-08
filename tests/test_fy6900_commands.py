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
    """WMF envoie la fréquence en µHz sur 14 chiffres (doc FY6900)."""

    def test_100_hz(self):
        # 100 Hz = 100_000_000 µHz (9 chiffres → 5 zéros à gauche)
        assert FY.format_wmf_hz(100) == "WMF00000100000000\n"

    def test_1000_hz(self):
        # 1000 Hz = 1_000_000_000 µHz ; format 14 chiffres (comportement selon Python)
        out = FY.format_wmf_hz(1000)
        assert out.startswith("WMF") and out.endswith("\n")
        assert len(out) == 3 + 14 + 1  # WMF (3) + 14 chiffres + \n
        # Valeur envoyée = 1000 * 1e6 = 1e9 µHz (vérification sémantique)
        assert FY._freq_hz_to_uhz(1000) == 1_000_000_000

    def test_freq_high(self):
        # 12345678.901234 Hz → arrondi µHz = 12345678901234 (14 chiffres)
        assert FY.format_wmf_hz(12345678.901234) == "WMF12345678901234\n"

    def test_clamp_negative(self):
        assert FY.format_wmf_hz(-1) == "WMF00000000000000\n"

    def test_fractional_hz(self):
        # 1.5 Hz = 1_500_000 µHz (7 chiffres → 7 zéros à gauche)
        assert FY.format_wmf_hz(1.5) == "WMF00000001500000\n"


class TestFormatWma:
    def test_amplitude(self):
        assert FY.format_wma(1.41) == "WMA1.410\n"
        assert FY.format_wma(5.0) == "WMA5.000\n"
        assert FY.format_wma(1.414) == "WMA1.414\n"


class TestFormatWmo:
    def test_offset_zero(self):
        assert FY.format_wmo(0) == "WMO0.00\n"


class TestFormatWmn:
    def test_on(self):
        assert FY.format_wmn(True) == "WMN1\n"

    def test_off(self):
        assert FY.format_wmn(False) == "WMN0\n"


class TestFormatWmdWfd:
    def test_duty(self):
        assert FY.format_wmd(50) == "WMD50.00\n"
        assert FY.format_wfd(25.5) == "WFD25.50\n"
        assert FY.format_wmd(100) == "WMD100.00\n"


class TestFormatWmpWfp:
    def test_phase(self):
        assert FY.format_wmp(0) == "WMP0.00\n"
        assert FY.format_wmp(90) == "WMP90.00\n"
        assert FY.format_wfp(180) == "WFP180.00\n"
