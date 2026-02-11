"""Tests du lissage (moving average, Savitzky-Golay)."""
import pytest

from ui.bode_csv_viewer.smoothing import (
    MovingAverageSmoother,
    smooth_savgol,
    has_savgol,
)


class TestMovingAverageSmoother:
    def test_window_property(self):
        s = MovingAverageSmoother(5)
        assert s.window == 5

    def test_window_clamped(self):
        s = MovingAverageSmoother(0)
        assert s.window == 1
        s2 = MovingAverageSmoother(20)
        assert s2.window == 11

    def test_smooth_empty(self):
        s = MovingAverageSmoother(5)
        assert s.smooth([]) == []

    def test_smooth_window_1(self):
        s = MovingAverageSmoother(1)
        assert s.smooth([1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0]

    def test_smooth_window_3(self):
        s = MovingAverageSmoother(3)
        out = s.smooth([1.0, 2.0, 3.0, 4.0, 5.0])
        assert out[2] == pytest.approx(3.0)
        assert len(out) == 5

    def test_set_window(self):
        s = MovingAverageSmoother(5)
        s.set_window(7)
        assert s.window == 7


class TestSmoothSavgol:
    def test_returns_copy_without_scipy(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        out = smooth_savgol(vals, 5)
        assert out == vals or len(out) == len(vals)

    def test_short_series_returns_copy(self):
        out = smooth_savgol([1.0, 2.0], 5)
        assert out == [1.0, 2.0]


def test_has_savgol():
    assert isinstance(has_savgol(), bool)
