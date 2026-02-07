"""
Tests de core.device_detection : list_serial_ports, update_config_ports, detect_devices (mocké).
"""
from unittest.mock import patch, MagicMock

import pytest

from core.device_detection import list_serial_ports, update_config_ports, detect_devices


class TestListSerialPorts:
    def test_returns_list_of_device_names(self):
        with patch("serial.tools.list_ports.comports") as mock_comports:
            mock_comports.return_value = [
                MagicMock(device="COM3"),
                MagicMock(device="COM4"),
            ]
            ports = list_serial_ports()
            assert ports == ["COM3", "COM4"]

    def test_empty_when_no_ports(self):
        with patch("serial.tools.list_ports.comports") as mock_comports:
            mock_comports.return_value = []
            assert list_serial_ports() == []


class TestUpdateConfigPorts:
    def test_updates_ports_in_copy(self):
        config = {
            "serial_multimeter": {"port": "COM1", "baudrate": 9600},
            "serial_generator": {"port": "COM2"},
        }
        out = update_config_ports(config, "COM3", "COM4")
        assert out is not config
        assert out["serial_multimeter"]["port"] == "COM3"
        assert out["serial_generator"]["port"] == "COM4"
        assert config["serial_multimeter"]["port"] == "COM1"

    def test_creates_sections_if_missing(self):
        out = update_config_ports({}, "COM1", "COM2")
        assert "serial_multimeter" in out
        assert "serial_generator" in out
        assert out["serial_multimeter"]["port"] == "COM1"
        assert out["serial_generator"]["port"] == "COM2"

    def test_none_port_does_not_overwrite(self):
        config = {"serial_multimeter": {"port": "COM1"}, "serial_generator": {"port": "COM2"}}
        out = update_config_ports(config, None, "COM4")
        assert out["serial_multimeter"]["port"] == "COM1"
        assert out["serial_generator"]["port"] == "COM4"


class TestDetectDevices:
    def test_returns_tuple_none_none_when_no_ports(self):
        with patch("core.device_detection.list_serial_ports", return_value=[]):
            m, g = detect_devices()
            assert m is None
            assert g is None

    def test_returns_ports_when_mocks_identify(self):
        with patch("core.device_detection.list_serial_ports", return_value=["COM3", "COM4"]):
            with patch("core.device_detection._try_owon_on_port") as try_owon:
                with patch("core.device_detection._try_fy6900_on_port") as try_fy:
                    try_owon.side_effect = lambda p: p == "COM3"
                    try_fy.side_effect = lambda p: p == "COM4"
                    m, g = detect_devices()
                    assert m == "COM3"
                    assert g == "COM4"
