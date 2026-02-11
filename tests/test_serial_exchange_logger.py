"""
Tests de core.serial_exchange_logger.SerialExchangeLogger.
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.serial_exchange_logger import SerialExchangeLogger


class TestSerialExchangeLogger:
    def test_log_creates_file_on_first_write(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        logger.log("terminal", "TX", "*IDN?")
        assert logger._path is not None
        assert logger._path.exists()
        content = logger._path.read_text(encoding="utf-8")
        assert "TX" in content
        assert "*IDN?" in content
        logger.close()

    def test_log_equipment_writes_header(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        logger.log_equipment("Multimètre (COM17)")
        content = logger._path.read_text(encoding="utf-8")
        assert "# Équipement: Multimètre (COM17)" in content
        logger.close()

    def test_get_callback_writes_via_log(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        cb = logger.get_callback("generator")
        cb("RX", "0.0\n")
        content = logger._path.read_text(encoding="utf-8")
        assert "RX" in content
        assert "0.0" in content
        logger.close()

    def test_close_closes_file(self, tmp_path):
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        logger.log("m", "TX", "x")
        logger.close()
        assert logger._file is None

    def test_close_handles_close_exception(self, tmp_path):
        """close() ne propage pas si _file.close() lève (couverture 52-53)."""
        logger = SerialExchangeLogger(log_dir=str(tmp_path))
        logger.log("m", "TX", "x")
        real_file = logger._file
        real_file.close()
        logger._file = MagicMock()
        logger._file.close = MagicMock(side_effect=OSError("Device error"))
        logger.close()
        assert logger._file is None
