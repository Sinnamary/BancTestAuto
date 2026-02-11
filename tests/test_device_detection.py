"""
Tests de core.device_detection : list_serial_ports, update_config_ports, detect_devices (mocké).
Après refactor, detect_devices délègue à core.detection ; les mocks ciblent les bons modules.
"""
from unittest.mock import patch, MagicMock

import pytest

from core.device_detection import list_serial_ports, update_config_ports, detect_devices
from core.detection.result import SerialDetectionResult


class TestListSerialPorts:
    def test_returns_list_of_device_names(self):
        with patch("core.detection.list_serial_ports", return_value=["COM3", "COM4"]):
            ports = list_serial_ports()
            assert ports == ["COM3", "COM4"]

    def test_empty_when_no_ports(self):
        with patch("core.detection.list_serial_ports", return_value=[]):
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
        with patch("core.detection.runner.list_serial_ports", return_value=[]):
            m, m_baud, g, g_baud, log_lines = detect_devices()
            assert m is None
            assert m_baud is None
            assert g is None
            assert g_baud is None
            assert isinstance(log_lines, list)

    def test_returns_ports_when_mocks_identify(self):
        with patch("core.detection.runner.list_serial_ports", return_value=["COM3", "COM4"]):
            with patch("core.detection.runner.detect_owon") as mock_owon:
                with patch("core.detection.runner.detect_fy6900") as mock_fy:
                    mock_owon.return_value = SerialDetectionResult(port="COM3", baudrate=115200)
                    mock_fy.return_value = SerialDetectionResult(port="COM4", baudrate=115200)
                    m, m_baud, g, g_baud, log_lines = detect_devices()
                    assert m == "COM3"
                    assert m_baud == 115200
                    assert g == "COM4"
                    assert g_baud == 115200
                    assert isinstance(log_lines, list)