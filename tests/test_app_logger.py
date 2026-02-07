"""
Tests de core.app_logger : get_logger, set_level, get_current_level_name, _level_from_config, init_app_logging.
"""
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from core.app_logger import (
    get_logger,
    set_level,
    get_current_level_name,
    LEVELS,
    init_app_logging,
)
from core.app_logger import _level_from_config


class TestLevelFromConfig:
    def test_default_info(self):
        assert _level_from_config({}) == logging.INFO
        assert _level_from_config({"logging": {}}) == logging.INFO

    def test_level_from_config(self):
        assert _level_from_config({"logging": {"level": "DEBUG"}}) == logging.DEBUG
        assert _level_from_config({"logging": {"level": "WARNING"}}) == logging.WARNING
        assert _level_from_config({"logging": {"level": "ERROR"}}) == logging.ERROR

    def test_unknown_level_falls_back_to_info(self):
        assert _level_from_config({"logging": {"level": "INVALID"}}) == logging.INFO


class TestGetLogger:
    def test_returns_logger_with_name(self):
        log = get_logger("test.module")
        assert log.name == "test.module"


class TestInitAppLogging:
    def test_creates_file_in_output_dir(self, tmp_path):
        config = {"logging": {"output_dir": str(tmp_path), "level": "INFO"}}
        init_app_logging(config)
        logs = list(tmp_path.glob("app_*.log"))
        assert len(logs) >= 1
        assert logs[0].exists()

    def test_idempotent_second_call_does_not_duplicate_handler(self, tmp_path):
        config = {"logging": {"output_dir": str(tmp_path), "level": "INFO"}}
        init_app_logging(config)
        root = logging.getLogger()
        n_before = len(root.handlers)
        init_app_logging(config)
        n_after = len(root.handlers)
        assert n_after == n_before


class TestSetLevelAndGetCurrentLevelName:
    def test_get_current_level_name_before_init(self):
        # Si _file_handler est None (module pas initialisé), retourne "INFO"
        with patch("core.app_logger._file_handler", None):
            assert get_current_level_name() == "INFO"

    def test_set_level_changes_handler_level(self):
        with patch("core.app_logger._file_handler") as mock_fh:
            mock_fh.level = logging.INFO
            set_level("DEBUG")
            mock_fh.setLevel.assert_called_with(logging.DEBUG)
