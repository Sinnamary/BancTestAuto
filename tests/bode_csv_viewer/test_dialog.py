"""Tests du dialogue Bode CSV viewer (open_viewer, panneaux, BodeCsvViewerDialog)."""
from pathlib import Path

import pytest

from ui.bode_csv_viewer import open_viewer
from ui.bode_csv_viewer.model import BodeCsvPoint, BodeCsvDataset
from ui.bode_csv_viewer.view_state import BodeViewOptions
from ui.bode_csv_viewer.panel_y_axis import build_y_axis_panel
from ui.bode_csv_viewer.panel_display import build_display_panel
from ui.bode_csv_viewer.panel_search import build_search_panel
from ui.bode_csv_viewer.panel_scale import build_scale_panel
from ui.bode_csv_viewer.panel_buttons import build_buttons_layout
from ui.bode_csv_viewer.dialog import BodeCsvViewerDialog


class TestOpenViewer:
    def test_empty_path_returns_immediately(self):
        open_viewer(None, "", None)
        open_viewer(None, "", {})

    def test_empty_csv_shows_warning_and_returns(self, bode_csv_dir):
        from unittest.mock import patch
        empty_csv = bode_csv_dir / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")
        with patch("ui.bode_csv_viewer.QMessageBox.warning") as mock_warn:
            open_viewer(None, str(empty_csv), None)
        mock_warn.assert_called_once()
        assert "Aucune donnée" in mock_warn.call_args[0][2] or ""

    def test_valid_csv_opens_dialog(self, bode_csv_dir, qapp_for_viewer):
        from unittest.mock import patch
        valid_csv = bode_csv_dir / "valid.csv"
        valid_csv.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n100.0;0.7;0.7;-3.0\n",
            encoding="utf-8",
        )
        with patch("ui.bode_csv_viewer.BodeCsvViewerDialog") as mock_dialog:
            mock_dialog.return_value.exec.return_value = None
            open_viewer(None, str(valid_csv), {})
        mock_dialog.assert_called_once()
        call_kw = mock_dialog.call_args[1]
        assert call_kw["csv_path"] == str(valid_csv)
        assert not call_kw["dataset"].is_empty()
        mock_dialog.return_value.exec.assert_called_once()


class TestPanelBuilders:
    @pytest.fixture
    def qapp(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_build_y_axis_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        gb = build_y_axis_panel(parent)
        assert hasattr(parent, "_y_linear")
        assert hasattr(parent, "_y_db")
        assert hasattr(parent, "_y_group")
        assert gb is not None

    def test_build_display_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        parent._options = BodeViewOptions.default()
        gb = build_display_panel(parent, lambda: None)
        assert hasattr(parent, "_background_combo")
        assert hasattr(parent, "_curve_color_combo")
        assert hasattr(parent, "_grid_cb")
        assert hasattr(parent, "_smooth_cb")
        assert hasattr(parent, "_peaks_cb")
        assert gb is not None

    def test_build_search_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        gb = build_search_panel(parent, lambda: None, lambda: None)
        assert hasattr(parent, "_target_gain_spin")
        assert hasattr(parent, "_search_target_btn")
        assert hasattr(parent, "_clear_target_btn")
        assert hasattr(parent, "_target_result_label")
        assert gb is not None

    def test_build_scale_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        gb = build_scale_panel(parent, lambda: None, lambda: None)
        assert hasattr(parent, "_f_min_spin")
        assert hasattr(parent, "_f_max_spin")
        assert hasattr(parent, "_gain_min_spin")
        assert hasattr(parent, "_apply_scale_btn")
        assert hasattr(parent, "_zoom_zone_cb")
        assert gb is not None

    def test_build_buttons_layout(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        parent.accept = lambda: None
        layout = build_buttons_layout(parent, lambda: None, lambda: None, lambda: None)
        assert hasattr(parent, "_adjust_btn")
        assert hasattr(parent, "_export_btn")
        assert hasattr(parent, "_export_csv_btn")
        assert hasattr(parent, "_close_btn")
        assert layout is not None


class TestBodeCsvViewerDialog:
    @pytest.fixture
    def qapp(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def small_dataset(self):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
            BodeCsvPoint(1000.0, 0.1, 0.1, -20.0),
        ]
        return BodeCsvDataset(pts)

    def test_dialog_creates_with_dataset(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=None)
        assert dlg._dataset.count == 3
        assert dlg._plot is not None
        dlg.close()

    def test_apply_bode_viewer_config_empty_no_op(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._apply_bode_viewer_config({})
        dlg.close()

    def test_apply_bode_viewer_config_applies_options(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._apply_bode_viewer_config({
            "plot_background_dark": False,
            "curve_color": "#e04040",
            "grid_visible": True,
            "grid_minor_visible": True,
            "smooth_window": 5,
            "show_raw_curve": True,
            "smooth_savgol": False,
            "y_linear": True,
            "peaks_visible": True,
        })
        dlg.close()

    def test_get_bode_viewer_state(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        state = dlg._get_bode_viewer_state()
        assert "plot_background_dark" in state
        assert "curve_color" in state
        assert "grid_visible" in state
        assert "y_linear" in state
        dlg.close()

    def test_save_bode_viewer_to_config(self, qapp, small_dataset):
        config = {}
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=config)
        dlg._save_bode_viewer_to_config()
        assert "bode_viewer" in config
        assert "curve_color" in config["bode_viewer"]
        dlg.close()

    def test_update_info_panel_empty(self, qapp):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=BodeCsvDataset([]), config={})
        dlg._update_info_panel()
        assert dlg._info_label.text() == ""
        dlg.close()

    def test_update_info_panel_with_data(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._update_info_panel()
        assert "G_max" in dlg._info_label.text() or "points" in dlg._info_label.text()
        dlg.close()

    def test_on_adjust_view_and_sync_scale(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._on_adjust_view()
        dlg._sync_scale_spins_from_view()
        dlg.close()

    def test_on_apply_scale(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._f_min_spin.setValue(10)
        dlg._f_max_spin.setValue(10000)
        dlg._gain_min_spin.setValue(-30)
        dlg._gain_max_spin.setValue(5)
        dlg._on_apply_scale()
        dlg.close()

    def test_on_apply_scale_corrects_inverted_range(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._f_min_spin.setValue(1000)
        dlg._f_max_spin.setValue(100)
        dlg._on_apply_scale()
        assert dlg._f_max_spin.value() >= dlg._f_min_spin.value()
        dlg.close()

    def test_on_zoom_zone_toggled(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._on_zoom_zone_toggled(True)
        dlg._on_zoom_zone_toggled(False)
        dlg.close()

    def test_on_search_target_gain(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._target_gain_spin.setValue(-3)
        dlg._on_search_target_gain()
        dlg._on_clear_target_gain()
        assert dlg._target_result_label.text() == ""
        dlg.close()

    def test_on_search_target_gain_empty_dataset(self, qapp):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=BodeCsvDataset([]), config={})
        dlg._on_search_target_gain()
        assert "aucune donnée" in dlg._target_result_label.text().lower()
        dlg.close()

    def test_on_export_csv_with_data(self, qapp, small_dataset, bode_csv_dir):
        from unittest.mock import patch
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        path = str(bode_csv_dir / "exported.csv")
        with patch("ui.bode_csv_viewer.dialog.QFileDialog.getSaveFileName", return_value=(path, "")):
            with patch("ui.bode_csv_viewer.dialog.QMessageBox.information"):
                dlg._on_export_csv()
        assert Path(path).exists()
        dlg.close()

    def test_on_export_csv_empty_dataset_shows_warning(self, qapp):
        from unittest.mock import patch
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=BodeCsvDataset([]), config={})
        with patch("ui.bode_csv_viewer.dialog.QMessageBox.warning") as mock_warn:
            dlg._on_export_csv()
        mock_warn.assert_called_once()
        dlg.close()

    def test_accept_saves_config(self, qapp, small_dataset):
        config = {}
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=config)
        dlg.accept()
        assert "bode_viewer" in config
        dlg.close()

    def test_reject_saves_config(self, qapp, small_dataset):
        config = {}
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=config)
        dlg.reject()
        assert "bode_viewer" in config
        dlg.close()

    def test_dialog_loads_csv_when_path_given_no_dataset(self, qapp, bode_csv_dir):
        valid_csv = bode_csv_dir / "load_test.csv"
        valid_csv.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n50.0;0.8;0.8;-1.9\n200.0;0.5;0.5;-6.0\n",
            encoding="utf-8",
        )
        dlg = BodeCsvViewerDialog(None, csv_path=str(valid_csv), dataset=None, config={})
        assert dlg._dataset.count == 2
        dlg.close()

    def test_on_export_png(self, qapp, small_dataset, bode_csv_dir):
        from unittest.mock import patch
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        path = str(bode_csv_dir / "graph.png")
        with patch("ui.bode_csv_viewer.dialog.QFileDialog.getSaveFileName", return_value=(path, "")):
            with patch("ui.bode_csv_viewer.dialog.QMessageBox.information"):
                dlg._on_export()
        dlg.close()
