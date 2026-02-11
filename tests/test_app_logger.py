"""
Tests de core.app_logger : get_logger, set_level, get_current_level_name, _level_from_config, init_app_logging.
"""
import logging
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from core.app_logger import (
    get_logger,
    set_level,
    get_current_level_name,
    get_latest_log_path,
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

    def test_get_current_level_name_after_init_returns_configured_level(self, tmp_path):
        """Après init, get_current_level_name() parcourt LEVELS et retourne le nom du niveau (couverture 90-94)."""
        config = {"logging": {"output_dir": str(tmp_path), "level": "INFO"}}
        init_app_logging(config)
        assert get_current_level_name() == "INFO"

    def test_get_current_level_name_after_set_level(self, tmp_path):
        config = {"logging": {"output_dir": str(tmp_path), "level": "DEBUG"}}
        init_app_logging(config)
        set_level("WARNING")
        assert get_current_level_name() == "WARNING"

    def test_set_level_changes_handler_level(self):
        with patch("core.app_logger._file_handler") as mock_fh:
            mock_fh.level = logging.INFO
            set_level("DEBUG")
            mock_fh.setLevel.assert_called_with(logging.DEBUG)

    def test_get_current_level_name_fallback_when_level_not_in_levels(self):
        """Si le handler a un niveau non présent dans LEVELS (ex. niveau personnalisé), retourne 'INFO'."""
        with patch("core.app_logger._file_handler") as mock_fh:
            mock_fh.level = 999  # niveau non dans LEVELS
            assert get_current_level_name() == "INFO"


class TestGetLatestLogPath:
    """get_latest_log_path : répertoire absent, aucun log, un ou plusieurs logs."""

    def test_returns_none_when_output_dir_does_not_exist(self):
        config = {"logging": {"output_dir": "/nonexistent/path/12345"}}
        assert get_latest_log_path(config) is None

    def test_returns_none_when_no_app_logs(self, tmp_path):
        config = {"logging": {"output_dir": str(tmp_path)}}
        (tmp_path / "other.txt").write_text("x")
        assert get_latest_log_path(config) is None

    def test_returns_most_recent_app_log(self, tmp_path):
        config = {"logging": {"output_dir": str(tmp_path)}}
        old_log = tmp_path / "app_2020-01-01_00-00-00.log"
        new_log = tmp_path / "app_2025-01-01_12-00-00.log"
        old_log.write_text("old")
        new_log.write_text("new")
        # Forcer mtime : le plus récent doit être new_log
        old_ts = time.time() - 3600
        new_ts = time.time()
        os.utime(old_log, (old_ts, old_ts))
        os.utime(new_log, (new_ts, new_ts))
        result = get_latest_log_path(config)
        assert result is not None
        assert result == new_log

    def test_uses_logging_section_from_config(self, tmp_path):
        config = {"logging": {"output_dir": str(tmp_path)}}
        log_file = tmp_path / "app_2025-01-01_00-00-00.log"
        log_file.write_text("log")
        assert get_latest_log_path(config) == log_file
