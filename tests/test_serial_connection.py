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
        self._in_waiting = 0

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

    def read(self, size=1):
        return b"\x00" * min(size, 1)

    @property
    def in_waiting(self):
        return self._in_waiting


class TestSerialConnection:
    def test_is_open_before_open(self):
        conn = SerialConnection(port="COM99")
        assert conn._serial is None
        assert conn.is_open() is False

    def test_open_and_is_open(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            assert conn.is_open() is False
            conn.open()
            assert conn.is_open() is True
            conn.close()
            assert conn.is_open() is False

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

    def test_update_params_timeout_and_write_timeout(self):
        conn = SerialConnection(port="COM1", timeout=1.0, write_timeout=2.0)
        conn.update_params(timeout=3.0, write_timeout=4.0)
        assert conn._timeout == 3.0
        assert conn._write_timeout == 4.0

    def test_in_waiting_when_closed_returns_zero(self):
        conn = SerialConnection(port="COM99")
        assert conn.in_waiting() == 0

    def test_in_waiting_when_open_returns_mock_value(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            conn.open()
            conn._serial._in_waiting = 5
            assert conn.in_waiting() == 5
            conn.close()

    def test_open_idempotent_does_not_reopen(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            conn.open()
            first_serial = conn._serial
            conn.open()
            assert conn._serial is first_serial

    def test_close_handles_exception(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            conn.open()
            conn._serial.close = MagicMock(side_effect=RuntimeError("busy"))
            conn.close()
            assert conn._serial is None

    def test_write_with_log_exchanges_calls_callback(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            callback = MagicMock()
            conn = SerialConnection(port="COM99", log_exchanges=True, log_callback=callback)
            conn.open()
            conn.write(b"*IDN?\n")
            callback.assert_called_once()
            assert callback.call_args[0][0] == "TX"
            conn.close()

    def test_readline_empty_does_not_call_log_callback_with_content(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99", log_exchanges=True, log_callback=MagicMock())
            conn.open()
            conn._serial.readline = MagicMock(return_value=b"")
            line = conn.readline()
            assert line == b""
            conn.close()

    def test_readline_with_data_calls_log_callback(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            callback = MagicMock()
            conn = SerialConnection(port="COM99", log_exchanges=True, log_callback=callback)
            conn.open()
            conn._serial.readline = MagicMock(return_value=b"OK\n")
            line = conn.readline()
            assert line == b"OK\n"
            assert callback.called
            conn.close()

    def test_read_until(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            conn.open()
            data = conn.read_until(b"\r\n")
            assert data == b"1.234\n"
            conn.close()

    def test_read(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            conn = SerialConnection(port="COM99")
            conn.open()
            data = conn.read(10)
            assert isinstance(data, bytes)
            conn.close()

    def test_read_with_log_exchanges_calls_callback(self):
        with patch("core.serial_connection.serial.Serial", MockSerial):
            callback = MagicMock()
            conn = SerialConnection(port="COM99", log_exchanges=True, log_callback=callback)
            conn.open()
            conn.read(5)
            callback.assert_called_once()
            assert callback.call_args[0][0] == "RX"
            conn.close()
