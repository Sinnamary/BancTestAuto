"""
Tests du module core.dos1102_commands : constantes et helpers SCPI oscilloscope DOS1102 (sans UI).
"""
import pytest

from core import dos1102_commands as CMD


class TestDos1102Constants:
    def test_idn(self):
        assert CMD.IDN == "*IDN?"

    def test_rst(self):
        assert "*RST" in CMD.RST

    def test_acq_modes(self):
        assert "SAMP" in CMD.ACQ_MODE_SAMP
        assert "PEAK" in CMD.ACQ_MODE_PEAK
        assert "AVE" in CMD.ACQ_MODE_AVE

    def test_ch1_ch2_coup(self):
        assert "CH1" in CMD.CH1_COUP_DC and "DC" in CMD.CH1_COUP_DC
        assert "CH2" in CMD.CH2_COUP_AC and "AC" in CMD.CH2_COUP_AC
        assert "GND" in CMD.CH1_COUP_GND

    def test_trigger(self):
        assert "TRIG" in CMD.TRIG_EDGE
        assert "SING" in CMD.TRIG_TYPE_SING

    def test_meas_query(self):
        assert "MEAS" in CMD.MEAS_QUERY

    def test_meas_types_tuple(self):
        assert "PERiod" in CMD.MEAS_TYPES
        assert "FREQuency" in CMD.MEAS_TYPES
        assert "PKPK" in CMD.MEAS_TYPES

    def test_meas_types_per_channel(self):
        assert isinstance(CMD.MEAS_TYPES_PER_CHANNEL, (list, tuple))
        assert len(CMD.MEAS_TYPES_PER_CHANNEL) > 0
        label, scpi = CMD.MEAS_TYPES_PER_CHANNEL[0]
        assert isinstance(label, str)
        assert isinstance(scpi, str)

    def test_waveform_commands(self):
        assert "WAV" in CMD.WAVEFORM_DATA_ALL or "DATA" in CMD.WAVEFORM_DATA_ALL
        assert "HEAD" in CMD.WAVEFORM_HEAD


class TestDos1102Helpers:
    def test_ch_coup(self):
        assert CMD.CH_COUP(1, "DC") == ":CH1:COUP DC"
        assert CMD.CH_COUP(2, "AC") == ":CH2:COUP AC"

    def test_ch_sca(self):
        assert "CH1" in CMD.CH_SCA(1, 0.5)
        assert "0.5" in CMD.CH_SCA(1, 0.5)

    def test_ch_pos(self):
        assert "CH2" in CMD.CH_POS(2, 0)

    def test_ch_offs(self):
        assert "OFFS" in CMD.CH_OFFS(1, 0.1)

    def test_ch_probe(self):
        assert CMD.CH_PROBE(1, "10X") == ":CH1:PROBE 10X"

    def test_ch_inv(self):
        assert "INV" in CMD.CH_INV(1, "ON")
        assert "OFF" in CMD.CH_INV(2, "OFF")

    def test_hor_offs(self):
        assert "HOR" in CMD.HOR_OFFS(0) and "OFFS" in CMD.HOR_OFFS(0)

    def test_hor_scal(self):
        assert "HOR" in CMD.HOR_SCAL(0.001)

    def test_waveform_screen_ch(self):
        assert CMD.WAVEFORM_SCREEN_CH(1) == ":DATA:WAVE:SCREEN:CH1?"
        assert CMD.WAVEFORM_SCREEN_CH(2) == ":DATA:WAVE:SCREEN:CH2?"

    def test_meas_ch_query(self):
        assert CMD.MEAS_CH_QUERY(1, "FREQuency") == ":MEAS:CH1:FREQuency?"
        assert CMD.MEAS_CH_QUERY(2, "PERiod") == ":MEAS:CH2:PERiod?"
