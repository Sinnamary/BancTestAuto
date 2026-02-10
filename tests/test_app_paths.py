"""
Tests du module core.app_paths : chemins racine et config (sans UI).
"""
from pathlib import Path

import pytest

from core.app_paths import get_base_path, get_config_path


class TestGetBasePath:
    def test_returns_path(self):
        p = get_base_path()
        assert isinstance(p, Path)
        assert p.is_absolute() or p == p.resolve()

    def test_contains_core_in_parent_structure(self):
        # En mode normal, la racine est le parent de core/
        p = get_base_path()
        # Soit core est un enfant de p, soit p est la racine du projet
        assert (p / "core").exists() or (p / "config").exists() or p.name == "BancTestAuto"

    def test_frozen_uses_meipass(self, monkeypatch):
        fake_meipass = Path("/tmp/pyinstaller_extract")
        monkeypatch.setattr("sys.frozen", True, raising=False)
        monkeypatch.setattr("sys._MEIPASS", str(fake_meipass), raising=False)
        p = get_base_path()
        assert str(p) == str(fake_meipass)


class TestGetConfigPath:
    def test_returns_path(self):
        p = get_config_path()
        assert isinstance(p, Path)

    def test_config_json_in_path(self):
        p = get_config_path()
        assert p.name == "config.json"

    def test_frozen_uses_exe_dir(self, monkeypatch):
        monkeypatch.setattr("sys.frozen", True, raising=False)
        monkeypatch.setattr("sys.executable", "/fake/dir/app.exe", raising=False)
        p = get_config_path()
        assert "config.json" in p.parts
        assert p.name == "config.json"
