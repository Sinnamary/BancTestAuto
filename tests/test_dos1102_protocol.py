"""
Tests du module core.dos1102_protocol : protocole SCPI oscilloscope DOS1102 (sans UI).
Connexion mockée.
"""
from unittest.mock import MagicMock

import pytest

from core.dos1102_protocol import Dos1102Protocol


class TestDos1102Protocol:
    def test_write_appends_newline(self):
        conn = MagicMock()
        conn.write = MagicMock()
        proto = Dos1102Protocol(conn)
        proto.write(":MEAS?")
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0]
        assert arg.endswith(b"\n")
        assert b"MEAS" in arg

    def test_ask_returns_decoded_stripped(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"1.234E+03\n")
        proto = Dos1102Protocol(conn)
        out = proto.ask("*IDN?")
        assert out == "1.234E+03"
        conn.write.assert_called_once()
        conn.readline.assert_called_once()

    def test_ask_strips_prompt_suffix(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"  HANMATEK,DOS1102->\n")
        proto = Dos1102Protocol(conn)
        out = proto.ask("*IDN?")
        assert out.endswith("DOS1102")
        assert "->" not in out

    def test_idn_sends_idn_command(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"*IDN?\n")
        proto = Dos1102Protocol(conn)
        proto.idn()
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "*IDN?" in call_arg

    def test_rst_writes_rst(self):
        conn = MagicMock()
        conn.write = MagicMock()
        proto = Dos1102Protocol(conn)
        proto.rst()
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "*RST" in call_arg

    def test_set_acq_samp_writes_command(self):
        conn = MagicMock()
        conn.write = MagicMock()
        proto = Dos1102Protocol(conn)
        proto.set_acq_samp()
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "SAMP" in call_arg

    def test_set_ch1_coupling_writes_dc(self):
        conn = MagicMock()
        conn.write = MagicMock()
        proto = Dos1102Protocol(conn)
        proto.set_ch1_coupling("DC")
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "CH1" in call_arg and "DC" in call_arg

    def test_set_ch_scale_writes_value(self):
        conn = MagicMock()
        conn.write = MagicMock()
        proto = Dos1102Protocol(conn)
        proto.set_ch_scale(1, 0.5)
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "CH1" in call_arg and "0.5" in call_arg

    def test_meas_ch_sends_and_returns(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"1000.0\n")
        proto = Dos1102Protocol(conn)
        out = proto.meas_ch(1, "FREQuency")
        assert out == "1000.0"
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "MEAS" in call_arg and "CH1" in call_arg and "FREQuency" in call_arg

    def test_meas_all_per_channel_returns_dict(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"0.001\n")
        proto = Dos1102Protocol(conn)
        result = proto.meas_all_per_channel(1)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_waveform_meta_data_parses_json(self):
        conn = MagicMock()
        conn.write = MagicMock()
        json_body = b'{"SAMPLE":{"DATALEN":"1400","SAMPLERATE":"1kS/s"},"CHANNEL":[{},{}],"TIMEBASE":{}}'
        conn.read = MagicMock(return_value=b"\n\x00\x00\x00\x00" + json_body)
        proto = Dos1102Protocol(conn)
        meta = proto.waveform_meta_data()
        assert meta["SAMPLE"]["DATALEN"] == "1400"
        assert "CHANNEL" in meta

    def test_waveform_screen_raw_reads_correct_size(self):
        conn = MagicMock()
        conn.write = MagicMock()
        n_points = 100
        conn.read = MagicMock(return_value=bytes(4 + 2 * n_points))
        proto = Dos1102Protocol(conn)
        raw = proto.waveform_screen_raw(1, n_points)
        assert len(raw) == 4 + 2 * n_points
        conn.read.assert_called_once_with(4 + 2 * n_points)
