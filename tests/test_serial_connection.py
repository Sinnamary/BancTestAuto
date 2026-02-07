"""
Tests de core.serial_connection.SerialConnection avec mock du port série.
"""
from unittest.mock import MagicMock, patch

import pytest
from serial import SerialException

from core.serial_connection import SerialConnection


class MockSerial:
    """Simule serial.Serial pour les tests sans matériel."""

    def __init__(self, **kwargs):
        self._open = True
        self._written = []

    @property
    def is_open(self):
        return self._open

    def close(self):
        self._open = False

    def write(self, data):
        self._written.append(data)
        return len(data)

    def readline(self):
        return b"1.234\n"

    def read_until(self, terminator=b"\n"):
        return b"1.234\n"


class TestSerialConnection:
    def test_is_open_before_open(self):
        conn = SerialConnection(port="COM99")
        assert conn._serial is None
        assert conn.is_open is False

    def test_open_and_is_open(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            assert conn.is_open is False
            conn.open()
            assert conn.is_open is True
            conn.close()
            assert conn.is_open is False

    def test_write_when_closed_raises(self):
        conn = SerialConnection(port="COM99")
        with pytest.raises(SerialException, match="non ouvert"):
            conn.write(b"x")

    def test_write_when_open_calls_serial(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            conn.open()
            n = conn.write(b"*IDN?\n")
            assert n == 6
            assert conn._serial._written == [b"*IDN?\n"]
            conn.close()

    def test_readline_when_closed_raises(self):
        conn = SerialConnection(port="COM99")
        with pytest.raises(SerialException, match="non ouvert"):
            conn.readline()

    def test_set_log_exchanges(self):
        conn = SerialConnection(port="COM99")
        conn.set_log_exchanges(True)
        assert conn._log_exchanges is True

    def test_update_params(self):
        conn = SerialConnection(port="COM1", baudrate=9600)
        conn.update_params(port="COM2", baudrate=115200)
        assert conn._port == "COM2"
        assert conn._baudrate == 115200
