"""Tests du style de plot (hover, courbes, style)."""
import pytest

from ui.bode_csv_viewer.model import BodeCsvPoint, BodeCsvDataset
from ui.bode_csv_viewer.plot_hover import format_hover_text
from ui.bode_csv_viewer.plot_curves import BodeCurveDrawer
from ui.bode_csv_viewer.plot_style import (
    BG_DARK,
    BG_LIGHT,
    AXIS_LABEL_FONT_SIZE,
    apply_axis_fonts,
    apply_background_style,
)


class TestFormatHoverText:
    def test_db_mode(self):
        s = format_hover_text(100.0, -3.0, y_linear=False)
        assert "dB" in s
        assert "100" in s
        assert "-3.00" in s

    def test_linear_mode(self):
        s = format_hover_text(1000.0, 0.707, y_linear=True)
        assert "Us/Ue" in s
        assert "kHz" in s
        assert "0.71" in s


class TestBodeCurveDrawer:
    @pytest.fixture
    def plot_item(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        yield pw.getPlotItem()
        pw.close()

    def test_clear(self, plot_item):
        drawer = BodeCurveDrawer(plot_item)
        drawer.clear()
        # pas d'exception

    def test_set_data_empty(self, plot_item):
        drawer = BodeCurveDrawer(plot_item)
        drawer.set_data(BodeCsvDataset([]), y_linear=False)
        drawer.set_data(BodeCsvDataset([]), y_linear=True)

    def test_set_data_with_points(self, plot_item):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
        ]
        ds = BodeCsvDataset(pts)
        drawer = BodeCurveDrawer(plot_item)
        drawer.set_data(ds, y_linear=False)
        drawer.set_data(ds, y_linear=True)

    def test_set_curve_color(self, plot_item):
        drawer = BodeCurveDrawer(plot_item)
        drawer.set_curve_color("#ff0000")
        from PyQt6.QtGui import QColor
        drawer.set_curve_color(QColor("#00ff00"))


class TestPlotStyle:
    def test_constants(self):
        assert BG_DARK == "k"
        assert BG_LIGHT == "w"
        assert AXIS_LABEL_FONT_SIZE == 12

    @pytest.fixture
    def plot_item(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        yield pw.getPlotItem()
        pw.close()

    def test_apply_axis_fonts(self, plot_item):
        apply_axis_fonts(plot_item)
        assert plot_item.getAxis("left").tickFont is not None

    def test_apply_background_style_dark(self, plot_item):
        vb = plot_item.getViewBox()
        grid = type("Grid", (), {"set_dark_background": lambda self, d: None})()
        apply_background_style(plot_item, vb, dark=True, grid=grid, hover_label=None)
        apply_background_style(plot_item, vb, dark=True, grid=grid, hover_label=None)

    def test_apply_background_style_light(self, plot_item):
        vb = plot_item.getViewBox()
        grid = type("Grid", (), {"set_dark_background": lambda self, d: None})()
        apply_background_style(plot_item, vb, dark=False, grid=grid, hover_label=None)

    def test_apply_background_style_with_hover_label(self, plot_item):
        import pyqtgraph as pg
        vb = plot_item.getViewBox()
        grid = type("Grid", (), {"set_dark_background": lambda self, d: None})()
        hover = pg.TextItem(text="")
        plot_item.addItem(hover)
        apply_background_style(plot_item, vb, dark=True, grid=grid, hover_label=hover)
        apply_background_style(plot_item, vb, dark=False, grid=grid, hover_label=hover)
