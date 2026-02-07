"""
Tests de core.data_logger.DataLogger : start, stop, is_running, callback.
"""
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.data_logger import DataLogger


class TestDataLogger:
    def test_is_running_initially_false(self):
        logger = DataLogger()
        assert logger.is_running() is False

    def test_start_without_measurement_returns_none(self):
        logger = DataLogger()
        assert logger.start() is None
        assert logger.start(output_dir="/tmp") is None

    def test_start_creates_file_and_returns_path(self, tmp_path):
        meas = MagicMock()
        meas.read_value = MagicMock(return_value="1.234")
        meas.parse_float = MagicMock(return_value=1.234)
        logger = DataLogger()
        logger.set_measurement(meas)
        path_str = logger.start(output_dir=str(tmp_path), interval_s=2.0)
        assert path_str is not None
        assert "owon_log_" in path_str
        assert path_str.endswith(".csv")
        assert logger.is_running() is True
        p = Path(path_str)
        assert p.exists()
        content = p.read_text(encoding="utf-8")
        assert "timestamp_iso" in content
        assert "elapsed_s" in content
        logger.stop()
        assert logger.is_running() is False

    def test_stop_closes_file(self, tmp_path):
        meas = MagicMock()
        meas.read_value = MagicMock(return_value="1.0")
        meas.parse_float = MagicMock(return_value=1.0)
        logger = DataLogger()
        logger.set_measurement(meas)
        logger.start(output_dir=str(tmp_path), interval_s=10.0)
        logger.stop()
        assert logger.is_running() is False

    def test_on_point_callback_called(self, tmp_path):
        meas = MagicMock()
        meas.read_value = MagicMock(return_value="2.5")
        meas.parse_float = MagicMock(return_value=2.5)
        logger = DataLogger()
        logger.set_measurement(meas)
        received = []

        def on_point(ts, elapsed, value, unit, mode):
            received.append((ts, elapsed, value, unit, mode))

        logger.set_on_point_callback(on_point)
        logger.start(output_dir=str(tmp_path), interval_s=0.5)
        time.sleep(0.8)
        logger.stop()
        assert len(received) >= 1
        assert received[0][2] == "2.5"
        assert received[0][3] == "V"
