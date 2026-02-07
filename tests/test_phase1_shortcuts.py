"""
Tests Phase 1 — Raccourcis clavier de la fenêtre principale.
Vérifie que les quatre raccourcis (F5, Ctrl+M, Ctrl+R, Ctrl+E) sont créés.
"""
import pytest

from PyQt6.QtGui import QShortcut
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    """Application Qt (une par module pour les tests MainWindow)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp):
    """Fenêtre principale (avec raccourcis)."""
    win = MainWindow()
    yield win


def _shortcut_keys(main_win):
    """Retourne l'ensemble des séquences de touches des raccourcis (chaînes)."""
    shortcuts = main_win.findChildren(QShortcut)
    return {s.key().toString() for s in shortcuts}


class TestMainWindowShortcuts:
    """Vérifie que les raccourcis documentés sont présents."""

    def test_shortcuts_exist(self, main_window):
        keys = _shortcut_keys(main_window)
        assert len(keys) >= 4

    def test_f5_shortcut(self, main_window):
        keys = _shortcut_keys(main_window)
        # PyQt peut retourner "F5" ou variante
        assert any("F5" in k or k == "F5" for k in keys)

    def test_ctrl_m_shortcut(self, main_window):
        keys = _shortcut_keys(main_window)
        assert any("M" in k and ("Ctrl" in k or "Control" in k) for k in keys)

    def test_ctrl_r_shortcut(self, main_window):
        keys = _shortcut_keys(main_window)
        assert any("R" in k and ("Ctrl" in k or "Control" in k) for k in keys)

    def test_ctrl_e_shortcut(self, main_window):
        keys = _shortcut_keys(main_window)
        assert any("E" in k and ("Ctrl" in k or "Control" in k) for k in keys)
