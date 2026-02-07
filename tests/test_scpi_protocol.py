"""
Tests de core.scpi_protocol.ScpiProtocol avec une SerialConnection mockée.
"""
from unittest.mock import MagicMock

import pytest

from core.scpi_protocol import ScpiProtocol


class TestScpiProtocol:
    def test_write_appends_newline_if_missing(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.write("CONF:VOLT:DC")
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0]
        assert arg.decode("utf-8").strip() == "CONF:VOLT:DC"
        assert arg.endswith(b"\n")

    def test_ask_sends_and_returns_decoded_line(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"1.234E+00\n")
        scpi = ScpiProtocol(conn)
        out = scpi.ask("*IDN?")
        assert out == "1.234E+00"
        assert conn.write.called
        assert conn.readline.called

    def test_idn_sends_idn_command(self):
        conn = MagicMock()
        conn.write = MagicMock()
        conn.readline = MagicMock(return_value=b"OWON,XDM2041,123\n")
        scpi = ScpiProtocol(conn)
        out = scpi.idn()
        assert "OWON" in out or "XDM" in out or "123" in out
        call_arg = conn.write.call_args[0][0].decode("utf-8")
        assert "*IDN?" in call_arg

    def test_set_volt_ac_writes_conf_and_auto(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.set_volt_ac()
        assert conn.write.call_count >= 2

    def test_rst_writes_rst_command(self):
        conn = MagicMock()
        conn.write = MagicMock()
        scpi = ScpiProtocol(conn)
        scpi.rst()
        conn.write.assert_called_once()
        arg = conn.write.call_args[0][0].decode("utf-8").strip()
        assert "*RST" in arg
