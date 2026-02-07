"""
Tests de la vue Enregistrement (Phase 4) : parsing CSV, pas d'erreur à l'import.
"""
import csv
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from PyQt6.QtWidgets import QApplication

from ui.views.logging_view import LoggingView, _HAS_PYQTGRAPH, LOAD_COLORS


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_has_pyqtgraph():
    assert _HAS_PYQTGRAPH is True


def test_load_colors_defined():
    assert len(LOAD_COLORS) >= 2
    assert all(isinstance(c, str) and c.startswith("#") for c in LOAD_COLORS)


def test_logging_view_builds(qapp):
    view = LoggingView()
    assert view._live_t == []
    assert view._live_y == []
    assert view._loaded_curves == []


def test_parse_log_csv_valid(tmp_path):
    """Le CSV produit par DataLogger est correctement parsé."""
    csv_path = tmp_path / "test_log.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_iso", "elapsed_s", "value", "unit", "mode"])
        w.writerow(["2025-02-07T12:00:00", "0.00", "1.234", "V", "VOLT:DC"])
        w.writerow(["2025-02-07T12:00:05", "5.00", "1.235", "V", "VOLT:DC"])
    view = LoggingView()
    t_list, y_list = view._parse_log_csv(csv_path)
    assert t_list is not None
    assert y_list is not None
    assert len(t_list) == 2
    assert len(y_list) == 2
    assert t_list[0] == 0.0
    assert t_list[1] == 5.0
    assert y_list[0] == 1.234
    assert y_list[1] == 1.235


def test_parse_log_csv_empty(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("timestamp_iso,elapsed_s,value,unit,mode\n", encoding="utf-8")
    view = LoggingView()
    t_list, y_list = view._parse_log_csv(csv_path)
    assert t_list is None
    assert y_list is None


def test_parse_log_csv_invalid_file():
    view = LoggingView()
    t_list, y_list = view._parse_log_csv(Path("/nonexistent/file.csv"))
    assert t_list is None
    assert y_list is None
