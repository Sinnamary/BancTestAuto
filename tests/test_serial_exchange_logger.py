"""
Tests de core.serial_exchange_logger.SerialExchangeLogger.
"""
from pathlib import Path

import pytest

from core.serial_exchange_logger import SerialExchangeLogger


class TestSerialExchangeLogger:
    def test_log_creates_file_on_first_write(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        logger.log("multimeter", "TX", "*IDN?")
        assert logger._path is not None
        assert logger._path.exists()
        content = logger._path.read_text(encoding="utf-8")
        assert "multimeter" in content
        assert "TX" in content
        assert "*IDN?" in content
        logger.close()

    def test_get_callback_writes_via_log(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        cb = logger.get_callback("generator")
        cb("RX", "0.0\n")
        content = logger._path.read_text(encoding="utf-8")
        assert "generator" in content
        assert "RX" in content
        logger.close()

    def test_close_closes_file(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        logger.log("m", "TX", "x")
        logger.close()
        assert logger._file is None
