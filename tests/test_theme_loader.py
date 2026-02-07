"""
Tests du chargeur de thèmes (Phase 1) — ui.theme_loader.
"""
from pathlib import Path

import pytest

from ui.theme_loader import get_resources_themes_dir, get_theme_stylesheet


class TestGetResourcesThemesDir:
    def test_returns_resources_themes_under_base(self):
        base = Path("/tmp/project")
        got = get_resources_themes_dir(base)
        assert got == base / "resources" / "themes"

    def test_default_base_is_project_root(self):
        got = get_resources_themes_dir()
        assert got.name == "themes"
        assert got.parent.name == "resources"


class TestGetThemeStylesheet:
    def test_dark_theme_exists_and_returns_non_empty(self):
        # Depuis la racine du projet (parent du dossier tests)
        base = Path(__file__).resolve().parent.parent
        content = get_theme_stylesheet("dark", base_path=base)
        assert isinstance(content, str)
        assert len(content) > 0
        assert "background-color" in content or "QMainWindow" in content

    def test_empty_theme_name_returns_empty_string(self):
        assert get_theme_stylesheet("") == ""
        assert get_theme_stylesheet("   ") == ""

    def test_light_theme_exists_and_returns_non_empty(self):
        base = Path(__file__).resolve().parent.parent
        content = get_theme_stylesheet("light", base_path=base)
        assert isinstance(content, str)
        assert len(content) > 0
        assert "background-color" in content or "QMainWindow" in content

    def test_unknown_theme_returns_empty_string(self):
        base = Path(__file__).resolve().parent.parent
        assert get_theme_stylesheet("unknown_theme_xyz", base_path=base) == ""

    def test_theme_name_normalized_to_lowercase(self):
        base = Path(__file__).resolve().parent.parent
        content_dark = get_theme_stylesheet("DARK", base_path=base)
        content_lower = get_theme_stylesheet("dark", base_path=base)
        assert content_dark == content_lower
        assert len(content_dark) > 0
