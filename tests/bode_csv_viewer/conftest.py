"""Fixtures partagées pour les tests Bode CSV viewer."""
from pathlib import Path

import pytest


@pytest.fixture
def bode_csv_dir():
    """Répertoire pour les CSV de test (dans le projet pour fiabilité sous sandbox)."""
    root = Path(__file__).resolve().parent.parent.parent  # projet
    d = root / "tests" / "tmp_bode_csv"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def qapp_for_viewer():
    """QApplication pour les tests qui ouvrent le viewer ou des dialogues."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
