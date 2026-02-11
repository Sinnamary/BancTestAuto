"""
Tests du module config.settings : chargement, sauvegarde, fusion, getters.
"""
import json
from pathlib import Path

import pytest

from config.settings import (
    DEFAULT_CONFIG_PATH,
    DEFAULTS,
    load_config,
    save_config,
    get_config_file_path,
    get_serial_multimeter_config,
    get_serial_generator_config,
    get_usb_oscilloscope_config,
    get_serial_power_supply_config,
    get_filter_test_config,
    get_generator_config,
    get_logging_config,
    get_bode_viewer_config,
)
from config.settings import _deep_merge, _resolve_config_path


class TestDeepMerge:
    """Test de la fusion récursive (loaded prime sur default)."""

    def test_empty_loaded_returns_copy_of_default(self):
        assert _deep_merge({"a": 1}, {}) == {"a": 1}

    def test_loaded_overrides_top_level(self):
        got = _deep_merge({"a": 1, "b": 2}, {"a": 10})
        assert got == {"a": 10, "b": 2}

    def test_nested_merge(self):
        default = {"serial_multimeter": {"port": "COM3", "baudrate": 9600}}
        loaded = {"serial_multimeter": {"port": "COM5"}}
        got = _deep_merge(default, loaded)
        assert got["serial_multimeter"]["port"] == "COM5"
        assert got["serial_multimeter"]["baudrate"] == 9600

    def test_loaded_list_replaces_default_list(self):
        got = _deep_merge({"x": [1, 2]}, {"x": [3]})
        assert got["x"] == [3]


class TestLoadConfig:
    """Chargement : fichier absent => défauts ; fichier présent => fusion."""

    def test_missing_file_returns_defaults(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        assert not path.exists()
        cfg = load_config(path)
        assert cfg["serial_multimeter"]["port"] == DEFAULTS["serial_multimeter"]["port"]
        assert "filter_test" in cfg
        assert cfg["filter_test"]["f_min_hz"] == 10

    def test_existing_file_merges_with_defaults(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"serial_multimeter": {"port": "COM9"}}, ensure_ascii=False))
        cfg = load_config(path)
        assert cfg["serial_multimeter"]["port"] == "COM9"
        assert cfg["serial_multimeter"]["baudrate"] == 9600

    def test_load_accepts_str_path(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{}")
        cfg = load_config(str(path))
        assert isinstance(cfg, dict)


class TestSaveConfig:
    """Sauvegarde : crée le répertoire si besoin, écrit du JSON valide."""

    def test_save_creates_file_and_dir(self, tmp_path):
        path = tmp_path / "sub" / "config.json"
        config = {"serial_multimeter": {"port": "COM1"}}
        save_config(config, path)
        assert path.exists()
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["serial_multimeter"]["port"] == "COM1"

    def test_save_preserves_unicode(self, tmp_path):
        path = tmp_path / "config.json"
        config = {"comment": "éàù"}
        save_config(config, path)
        assert "éàù" in path.read_text(encoding="utf-8")


class TestGetters:
    """Chaque getter retourne une copie de la section avec défauts si absente."""

    def test_get_serial_multimeter_config(self):
        cfg = {}
        out = get_serial_multimeter_config(cfg)
        assert out["port"] == "COM3"
        out["port"] = "X"
        assert get_serial_multimeter_config(cfg)["port"] == "COM3"

    def test_get_serial_generator_config(self):
        out = get_serial_generator_config({})
        assert out["baudrate"] == 115200

    def test_get_filter_test_config(self):
        out = get_filter_test_config({})
        assert out["f_min_hz"] == 10
        assert out["scale"] == "log"

    def test_get_generator_config(self):
        out = get_generator_config({})
        assert out["waveform"] == 0
        assert out["amplitude_v_peak"] == 1.414

    def test_get_logging_config(self):
        out = get_logging_config({})
        assert out["output_dir"] == "./logs"
        assert out["level"] == "INFO"

    def test_get_usb_oscilloscope_config(self):
        out = get_usb_oscilloscope_config({})
        assert out["vendor_id"] == 0x5345
        assert out["product_id"] == 0x1234
        out["read_timeout_ms"] = 999
        assert get_usb_oscilloscope_config({})["read_timeout_ms"] == 5000

    def test_get_serial_power_supply_config(self):
        out = get_serial_power_supply_config({})
        assert out["port"] == "COM6"
        assert out["baudrate"] == 9600

    def test_get_bode_viewer_config(self):
        out = get_bode_viewer_config({})
        assert "bode_viewer" in DEFAULTS
        # Section peut contenir options affichage / échelle
        out_custom = get_bode_viewer_config({"bode_viewer": {"y_scale": "linear"}})
        assert out_custom.get("y_scale") == "linear"


class TestResolveConfigPath:
    """_resolve_config_path et get_config_file_path."""

    def test_resolve_explicit_path(self, tmp_path):
        p = tmp_path / "my_config.json"
        p.write_text("{}")
        assert _resolve_config_path(str(p)) == p.resolve()
        assert _resolve_config_path(p) == p.resolve()

    def test_get_config_file_path_returns_resolved(self, tmp_path):
        p = tmp_path / "custom.json"
        assert get_config_file_path(p) == p.resolve()
        assert get_config_file_path(str(p)) == p.resolve()

    def test_resolve_fallback_cwd_config_when_default_missing(self, tmp_path, monkeypatch):
        # DEFAULT_CONFIG_PATH n'existe pas ; cwd/config/config.json existe => repli
        monkeypatch.setattr("config.settings.DEFAULT_CONFIG_PATH", tmp_path / "nonexistent.json")
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        fallback_file = config_dir / "config.json"
        fallback_file.write_text("{}")
        monkeypatch.chdir(tmp_path)
        # _resolve_config_path(None) doit utiliser le repli cwd/config/config.json
        resolved = _resolve_config_path(None)
        assert resolved == (tmp_path / "config" / "config.json")

    def test_resolve_returns_default_when_neither_default_nor_fallback_exist(self, tmp_path, monkeypatch):
        # Ni DEFAULT ni cwd/config/config.json n'existent => retourne DEFAULT pour message d'erreur cohérent
        default_path = tmp_path / "no_default.json"
        monkeypatch.setattr("config.settings.DEFAULT_CONFIG_PATH", default_path)
        monkeypatch.chdir(tmp_path)
        # ne pas créer config/config.json
        resolved = _resolve_config_path(None)
        assert resolved == default_path
