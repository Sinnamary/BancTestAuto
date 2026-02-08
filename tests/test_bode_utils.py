"""
Tests du module core.bode_utils : lissage et détection fréquence de coupure -3 dB.
"""
import pytest

from core.bode_utils import moving_average_smooth, find_cutoff_3db, find_peaks_and_valleys


class TestMovingAverageSmooth:
    def test_window_1_returns_copy(self):
        vals = [1.0, 2.0, 3.0]
        assert moving_average_smooth(vals, 1) == [1.0, 2.0, 3.0]

    def test_window_3_center(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        out = moving_average_smooth(vals, 3)
        assert out[0] == 1.5  # (1+2)/2
        assert out[2] == 3.0  # (2+3+4)/3
        assert out[4] == 4.5  # (4+5)/2

    def test_empty_returns_empty(self):
        assert moving_average_smooth([], 5) == []
        assert moving_average_smooth([1, 2, 3], 0) == [1, 2, 3]


class TestFindCutoff3db:
    def test_finds_cutoff_interpolated(self):
        freqs = [10, 100, 1000, 2000]
        gains = [0, -1, -3.5, -10]
        r = find_cutoff_3db(freqs, gains)
        assert r is not None
        fc, g = r
        assert 100 < fc < 1000
        assert g == pytest.approx(-3.0)

    def test_gain_ref_explicit(self):
        freqs = [100, 500, 1000]
        gains = [0, -3, -6]
        r = find_cutoff_3db(freqs, gains, gain_ref=0)
        assert r is not None
        fc, g = r
        assert g == pytest.approx(-3.0)

    def test_empty_returns_none(self):
        assert find_cutoff_3db([], []) is None
        assert find_cutoff_3db([1], [0]) is None

    def test_never_below_threshold_returns_none(self):
        freqs = [10, 100, 1000]
        gains = [0, -1, -2]
        assert find_cutoff_3db(freqs, gains) is None


class TestFindPeaksAndValleys:
    def test_finds_peak(self):
        freqs = [1, 2, 3, 4, 5, 6, 7]
        gains = [0, 1, 2, 5, 2, 1, 0]
        out = find_peaks_and_valleys(freqs, gains, order=2)
        assert any(kind == "pic" for _, _, kind in out)
        assert any(f == 4 for f, _, _ in out)
