"""
Tests du module core.version : métadonnées application (sans UI).
"""
import pytest

from core.version import APP_NAME, __version__, __version_date__, get_version_date


class TestVersionConstants:
    def test_app_name(self):
        assert isinstance(APP_NAME, str)
        assert "Banc" in APP_NAME or "test" in APP_NAME.lower()

    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3
        for p in parts:
            assert p.isdigit()

    def test_version_date_string_or_none(self):
        assert __version_date__ is None or isinstance(__version_date__, str)


class TestGetVersionDate:
    def test_returns_string(self):
        d = get_version_date()
        assert isinstance(d, str)

    def test_iso_like_when_set(self):
        d = get_version_date()
        # Format ISO ou date du jour
        assert len(d) >= 8
        assert d[4] == "-" or d.count("-") >= 2  # YYYY-MM-DD

    def test_when_version_date_none_returns_today(self, monkeypatch):
        monkeypatch.setattr("core.version.__version_date__", None)
        from datetime import date
        from core.version import get_version_date as gvd
        d = gvd()
        assert d == date.today().isoformat()
