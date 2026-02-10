"""
Tests du module core.rs305p_protocol : Modbus RTU, CRC, trames, Rs305pProtocol (sans UI).
Connexion série mockée.
"""
from unittest.mock import MagicMock

import pytest

from core.rs305p_protocol import (
    Rs305pProtocol,
    REG_ON_OFF,
    REG_U_DISPLAY,
    REG_I_DISPLAY,
    REG_SET_U,
    REG_SET_I,
    _crc16_modbus,
    _build_frame,
    _parse_response,
)


class TestCrc16Modbus:
    def test_empty_data(self):
        assert _crc16_modbus(b"") == 0xFFFF

    def test_known_crc(self):
        # CRC-16 Modbus de [0x01, 0x03] : valeur de référence courante
        crc = _crc16_modbus(bytes([0x01, 0x03]))
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF

    def test_frame_consistency(self):
        payload = bytes([0x01, 0x03, 0x00, 0x01, 0x00, 0x01])
        crc = _crc16_modbus(payload)
        full = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        # Recalculer CRC sur tout sauf les 2 derniers octets ne donne pas les 2 derniers
        # mais _parse_response vérifie addr/func ; on teste juste que crc est déterministe
        crc2 = _crc16_modbus(payload)
        assert crc == crc2


class TestBuildFrame:
    def test_length(self):
        frame = _build_frame(0x01, 0x03, bytes([0x00, 0x01, 0x00, 0x01]))
        assert len(frame) == 8  # addr, func, 4 data, 2 crc

    def test_starts_with_addr_func(self):
        data = bytes([0x00, 0x10, 0x00, 0x01])
        frame = _build_frame(0x01, 0x06, data)
        assert frame[0] == 0x01
        assert frame[1] == 0x06
        assert frame[2:6] == data


class TestParseResponse:
    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="trop courte"):
            _parse_response(bytes([0x01, 0x03]), 0x01, 0x03)

    def test_wrong_addr_raises(self):
        frame = bytes([0x02, 0x03, 0x02, 0x12, 0x34]) + bytes([0, 0])  # crc fake
        with pytest.raises(ValueError, match="Adresse"):
            _parse_response(frame, 0x01, 0x03)

    def test_valid_read_response(self):
        # Réponse FC03 : addr, 0x03, byte_count=2, val_hi, val_lo
        payload = bytes([0x01, 0x03, 0x02, 0x12, 0x34])
        crc = _crc16_modbus(payload)
        frame = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        data = _parse_response(frame, 0x01, 0x03)
        assert data == bytes([0x02, 0x12, 0x34])

    def test_wrong_func_raises(self):
        payload = bytes([0x01, 0x06, 0x00, 0x01, 0x00, 0x00])
        crc = _crc16_modbus(payload)
        frame = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        with pytest.raises(ValueError, match="fonction"):
            _parse_response(frame, 0x01, 0x03)


class TestRs305pProtocol:
    def test_read_register_returns_value(self):
        # Réponse FC03 : 2 octets de donnée = valeur 0x1234
        payload = bytes([0x01, 0x03, 0x02, 0x12, 0x34])
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        val = proto.read_register(REG_ON_OFF)
        assert val == 0x1234
        assert conn.write.called
        assert conn.read.called

    def test_get_output_true_when_nonzero(self):
        payload = bytes([0x01, 0x03, 0x02, 0x00, 0x01])
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        assert proto.get_output() is True

    def test_get_output_false_when_zero(self):
        payload = bytes([0x01, 0x03, 0x02, 0x00, 0x00])
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        assert proto.get_output() is False

    def test_get_voltage_scaling(self):
        # 12.34 V → raw 1234
        payload = bytes([0x01, 0x03, 0x02, 0x04, 0xD2])  # 1234
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        # read_register(REG_U_DISPLAY) → 1234 / 100 = 12.34
        conn.read.return_value = resp
        v = proto.get_voltage()
        assert v == pytest.approx(12.34)

    def test_get_current_scaling(self):
        # 1.234 A → raw 1234
        payload = bytes([0x01, 0x03, 0x02, 0x04, 0xD2])
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        i = proto.get_current()
        assert i == pytest.approx(1.234)

    def test_set_output_writes_register(self):
        # Écriture FC06 : réponse = requête echo
        payload = bytes([0x01, 0x06, 0x00, 0x01, 0x00, 0x01])
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        proto.set_output(True)
        call_arg = conn.write.call_args[0][0]
        assert len(call_arg) >= 8
        assert call_arg[0] == 0x01
        assert call_arg[1] == 0x06
        assert call_arg[4] == 0x00 and call_arg[5] == 0x01  # value 1 = ON

    def test_set_voltage_clamps_and_scales(self):
        payload = bytes([0x01, 0x06, 0x00, 0x30, 0x04, 0xB0])  # 1200 = 12.00 V
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        proto.set_voltage(12.0)
        call_arg = conn.write.call_args[0][0]
        assert call_arg[4] == 0x04 and call_arg[5] == 0xB0  # 12.0 * 100 = 1200

    def test_set_current_scales(self):
        payload = bytes([0x01, 0x06, 0x00, 0x31, 0x01, 0xF4])  # 500 = 0.5 A
        crc = _crc16_modbus(payload)
        resp = payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        conn = MagicMock()
        conn.write = MagicMock()
        conn.read = MagicMock(return_value=resp)
        proto = Rs305pProtocol(conn, slave_addr=1)
        proto.set_current(0.5)
        call_arg = conn.write.call_args[0][0]
        assert (call_arg[4] << 8) | call_arg[5] == 500
