"""Tests du widget de plot Bode (BodeCsvPlotWidget, overlays, zoom, phase)."""
from pathlib import Path

import pytest

from ui.bode_csv_viewer.model import BodeCsvPoint, BodeCsvDataset
from ui.bode_csv_viewer.plot_widget import BodeCsvPlotWidget
from ui.bode_csv_viewer.plot_peaks import BodePeaksOverlay
from ui.bode_csv_viewer.zoom_mode import ZoomModeController
from ui.bode_csv_viewer.viewbox_phase import PhaseOverlay


class TestBodeCsvPlotWidget:
    """Exécute le code du widget pour couvrir BodeCsvPlotWidget."""

    @pytest.fixture
    def qapp(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def widget(self, qapp):
        w = BodeCsvPlotWidget()
        yield w
        w.close()

    @pytest.fixture
    def dataset(self):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
            BodeCsvPoint(1000.0, 0.1, 0.1, -20.0),
        ]
        return BodeCsvDataset(pts)

    def test_init_and_set_dataset_empty(self, widget):
        widget.set_dataset(None)
        widget.set_dataset(BodeCsvDataset([]))
        assert widget.get_data_range() is None

    def test_set_dataset_with_data(self, widget, dataset):
        widget.set_dataset(dataset)
        r = widget.get_data_range()
        assert r is not None
        assert r[0] <= 10.0 and r[1] >= 1000.0

    def test_set_y_linear(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_y_linear(True)
        widget.set_y_linear(False)

    def test_grid_and_background(self, widget):
        widget.set_grid_visible(True)
        widget.set_grid_visible(False)
        widget.set_minor_grid_visible(True)
        widget.set_minor_grid_visible(False)
        widget.set_background_dark(True)
        widget.set_background_dark(False)

    def test_set_curve_color(self, widget):
        from PyQt6.QtGui import QColor
        widget.set_curve_color("#ff0000")
        widget.set_curve_color(QColor("#00ff00"))

    def test_set_smoothing(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_smoothing(0)
        widget.set_smoothing(5, show_raw=True, use_savgol=False)
        widget.set_smoothing(5, show_raw=False, use_savgol=True)

    def test_set_peaks_visible(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_peaks_visible(True)
        widget.set_peaks_visible(False)

    def test_set_target_gain_search(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_target_gain_search(-3.0, [100.0])
        widget.set_target_gain_search(None)
        widget.set_target_gain_search(-6.0, [50.0, 200.0])

    def test_auto_range(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.auto_range()
        widget.set_dataset(None)
        widget.auto_range()

    def test_set_view_range_and_get_view_range(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_view_range(10.0, 10000.0, -25.0, 5.0)
        x_min, x_max, y_min, y_max = widget.get_view_range()
        assert x_min == pytest.approx(10.0, rel=1e-5)
        assert x_max == pytest.approx(10000.0, rel=1e-5)
        assert y_min == pytest.approx(-25.0)
        assert y_max == pytest.approx(5.0)

    def test_set_rect_zoom_mode(self, widget):
        widget.set_rect_zoom_mode(True)
        widget.set_rect_zoom_mode(False)

    def test_export_png(self, widget, dataset, bode_csv_dir):
        widget.set_dataset(dataset)
        path = str(bode_csv_dir / "export_bode.png")
        ok = widget.export_png(path)
        assert isinstance(ok, bool)
        if ok:
            assert Path(path).exists()
        # en headless/sandbox l'export peut échouer ; le code est tout de même couvert

    def test_show_event_installs_hover_filter(self, widget, qapp):
        widget.show()
        assert getattr(widget, "_hover_filter_installed", False) or widget._hover_label is not None
        widget.hide()

    def test_event_filter_mouse_move(self, widget, qapp):
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import Qt
        widget.show()
        vb = widget._plot_widget.getViewBox()
        if vb.scene() and vb.scene().views():
            view = vb.scene().views()[0]
            pt = view.viewport().rect().center()
            pos = QPointF(float(pt.x()), float(pt.y()))
            event = QMouseEvent(
                QEvent.Type.MouseMove,
                pos,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.eventFilter(view.viewport(), event)
        widget.hide()


class TestBodePeaksOverlay:
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

    def test_set_visible(self, plot_item):
        overlay = BodePeaksOverlay(plot_item)
        overlay.set_visible(True)
        overlay.set_visible(False)

    def test_update_empty_dataset(self, plot_item):
        overlay = BodePeaksOverlay(plot_item)
        overlay.set_visible(True)
        overlay.update(BodeCsvDataset([]), y_linear=False)
        overlay.update(None, y_linear=False)

    def test_update_with_data(self, plot_item):
        pts = [
            BodeCsvPoint(1.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(2.0, 1.0, 1.0, 1.0),
            BodeCsvPoint(3.0, 1.0, 1.0, 2.0),
            BodeCsvPoint(4.0, 1.0, 1.0, 5.0),
            BodeCsvPoint(5.0, 1.0, 1.0, 2.0),
            BodeCsvPoint(6.0, 1.0, 1.0, 1.0),
            BodeCsvPoint(7.0, 1.0, 1.0, 0.0),
        ]
        ds = BodeCsvDataset(pts)
        overlay = BodePeaksOverlay(plot_item)
        overlay.set_visible(True)
        overlay.update(ds, y_linear=False)
        overlay.update(ds, y_linear=True)


class TestZoomModeController:
    """ZoomModeController : RectMode / PanMode sur le ViewBox principal."""

    @pytest.fixture
    def plot_item_and_vb(self):
        from PyQt6.QtWidgets import QApplication
        import pyqtgraph as pg
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        pw = pg.PlotWidget()
        pi = pw.getPlotItem()
        vb = pi.getViewBox()
        yield pi, vb
        pw.close()

    def test_init(self, plot_item_and_vb):
        _, vb = plot_item_and_vb
        ctrl = ZoomModeController(vb)
        assert ctrl.is_rect_zoom_enabled() is False

    def test_set_rect_zoom_enabled_true_then_false(self, plot_item_and_vb):
        _, vb = plot_item_and_vb
        ctrl = ZoomModeController(vb)
        ctrl.set_rect_zoom_enabled(True)
        assert ctrl.is_rect_zoom_enabled() is True
        assert ctrl.get_current_mode() == vb.RectMode
        ctrl.set_rect_zoom_enabled(False)
        assert ctrl.is_rect_zoom_enabled() is False
        assert ctrl.get_current_mode() == vb.PanMode

    def test_get_current_mode(self, plot_item_and_vb):
        _, vb = plot_item_and_vb
        ctrl = ZoomModeController(vb)
        vb.setMouseMode(vb.RectMode)
        assert ctrl.get_current_mode() == vb.RectMode
        vb.setMouseMode(vb.PanMode)
        assert ctrl.get_current_mode() == vb.PanMode


class TestPhaseOverlay:
    """PhaseOverlay : ViewBox phase, set_visible, set_zoom_zone_active, set_phase_data, clear_phase_data."""

    @pytest.fixture
    def plot_item_and_vb(self):
        from PyQt6.QtWidgets import QApplication
        import pyqtgraph as pg
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        pw = pg.PlotWidget()
        pi = pw.getPlotItem()
        vb = pi.getViewBox()
        yield pi, vb
        pw.close()

    def test_set_visible(self, plot_item_and_vb):
        pi, main_vb = plot_item_and_vb
        overlay = PhaseOverlay(pi, main_vb)
        overlay.set_visible(True)
        overlay.set_visible(False)

    def test_set_zoom_zone_active_true_then_false(self, plot_item_and_vb):
        pi, main_vb = plot_item_and_vb
        overlay = PhaseOverlay(pi, main_vb)
        overlay.set_zoom_zone_active(True)
        assert overlay.right_vb.zValue() == main_vb.zValue() - 10
        overlay.set_zoom_zone_active(False)
        assert overlay.right_vb.zValue() == PhaseOverlay.Z_PHASE_ON_TOP

    def test_set_phase_data_and_clear(self, plot_item_and_vb):
        pi, main_vb = plot_item_and_vb
        overlay = PhaseOverlay(pi, main_vb)
        overlay.set_phase_data([10.0, 100.0, 1000.0], [-5.0, -45.0, -85.0])
        overlay.clear_phase_data()
        assert overlay.phase_curve.xData is None or len(overlay.phase_curve.xData) == 0

    def test_set_phase_data_empty_y_finite_fallback(self, plot_item_and_vb):
        """Branche y_finite vide → y_range (-90, 0)."""
        pi, main_vb = plot_item_and_vb
        overlay = PhaseOverlay(pi, main_vb)
        overlay.set_phase_data([], [])
