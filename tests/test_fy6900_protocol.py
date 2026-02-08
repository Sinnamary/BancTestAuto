"""
Tests de core.fy6900_protocol.Fy6900Protocol avec SerialConnection mockée.
"""
from unittest.mock import MagicMock

import pytest

from core.fy6900_protocol import Fy6900Protocol


class TestFy6900Protocol:
    def test_send_encodes_utf8(self):
        conn = MagicMock()
        conn.write = MagicMock()
        fy = Fy6900Protocol(conn)
        fy._send("WMW00\n")
        conn.write.assert_called_once_with(b"WMW00\n")

    def test_set_waveform(self):
        conn = MagicMock()
        conn.write = MagicMock()
        fy = Fy6900Protocol(conn)
        fy.set_waveform(0)
        conn.write.assert_called_once()
        assert b"WMW00" in conn.write.call_args[0][0]

    def test_set_frequency_hz(self):
        conn = MagicMock()
        conn.write = MagicMock()
        fy = Fy6900Protocol(conn)
        fy.set_frequency_hz(100)
        conn.write.assert_called_once()
        assert b"WMF" in conn.write.call_args[0][0]

    def test_set_output_on_off(self):
        conn = MagicMock()
        conn.write = MagicMock()
        fy = Fy6900Protocol(conn)
        fy.set_output(True)
        assert b"WMN1" in conn.write.call_args[0][0]
        fy.set_output(False)
        assert b"WMN0" in conn.write.call_args[0][0]

    def test_set_output_channel_2_sends_wfn(self):
        conn = MagicMock()
        conn.write = MagicMock()
        fy = Fy6900Protocol(conn)
        fy.set_output(True, channel=2)
        assert b"WFN1" in conn.write.call_args[0][0]
        fy.set_output(False, channel=2)
        assert b"WFN0" in conn.write.call_args[0][0]

    def test_apply_sinus_1v_rms_sends_several_commands(self):
        conn = MagicMock()
        conn.write = MagicMock()
        fy = Fy6900Protocol(conn)
        fy.apply_sinus_1v_rms(1000.0)
        assert conn.write.call_count >= 4
        written = b"".join(c[0][0] for c in conn.write.call_args_list)
        assert b"WMW00" in written
        assert b"WMA" in written
        assert b"WMN1" in written
