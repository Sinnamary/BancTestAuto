"""Tests des formateurs (fréquence, etc.)."""
from ui.bode_csv_viewer.formatters import format_freq_hz


class TestFormatFreqHz:
    def test_hz(self):
        assert format_freq_hz(50.0) == "50.0 Hz"
        assert format_freq_hz(1.0) == "1.0 Hz"

    def test_khz(self):
        assert format_freq_hz(1000.0) == "1.00 kHz"
        assert "kHz" in format_freq_hz(2500.0)

    def test_mhz(self):
        assert "mHz" in format_freq_hz(0.5)
        assert format_freq_hz(0.001) == "1.0 mHz"
