"""Tests de la plage de vue (compute_data_range, apply_view_range, read_view_range)."""
import pytest

from ui.bode_csv_viewer.plot_range import (
    compute_data_range,
    apply_view_range,
    read_view_range,
    AUTO_RANGE_MARGIN,
)


class TestComputeDataRange:
    def test_empty_returns_none(self):
        assert compute_data_range([], []) is None
        assert compute_data_range([1], []) is None
        assert compute_data_range([], [1]) is None

    def test_length_mismatch_returns_none(self):
        assert compute_data_range([1, 2], [1]) is None

    def test_basic(self):
        r = compute_data_range([10.0, 1000.0], [0.0, -20.0])
        assert r is not None
        x_min, x_max, y_min, y_max = r
        assert x_min < 10.0
        assert x_max > 1000.0
        assert y_min < -20.0
        assert y_max > 0.0

    def test_x_min_floor(self):
        r = compute_data_range([1.0, 10.0], [0.0, 0.0])
        assert r is not None
        assert r[0] >= 0.1

    def test_margin_parameter(self):
        r0 = compute_data_range([10, 100], [0, -10], margin=0.0)
        r1 = compute_data_range([10, 100], [0, -10], margin=0.1)
        assert r0 is not None and r1 is not None
        assert r1[1] - r1[0] > r0[1] - r0[0]


class TestApplyAndReadViewRange:
    """Tests avec ViewBox pyqtgraph (nécessite Qt)."""

    @pytest.fixture
    def view_box(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        pw.setLogMode(x=True, y=False)
        vb = pw.getViewBox()
        yield vb
        pw.close()

    def test_apply_then_read_roundtrip(self, view_box):
        apply_view_range(view_box, 10.0, 10000.0, -20.0, 5.0, log_mode_x=True)
        out = read_view_range(view_box, log_mode_x=True)
        assert out[0] == pytest.approx(10.0, rel=1e-5)
        assert out[1] == pytest.approx(10000.0, rel=1e-5)
        assert out[2] == pytest.approx(-20.0)
        assert out[3] == pytest.approx(5.0)

    def test_read_with_fallback(self, view_box):
        fallback = (1.0, 1000.0, -10.0, 0.0)
        out = read_view_range(view_box, log_mode_x=True, fallback=fallback)
        assert len(out) == 4
        if out[0] < 1e-200 or out[1] > 1e200:
            assert out == fallback
        else:
            assert out[0] == pytest.approx(fallback[0]) or out == fallback
