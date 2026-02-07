"""
Tests du module core.filter_sweep : génération des fréquences (log / lin).
"""
import pytest

from core.filter_sweep import sweep_frequencies


class TestSweepFrequencies:
    def test_n_points_zero_returns_empty(self):
        assert sweep_frequencies(10, 1000, 0) == []
        assert sweep_frequencies(10, 1000, 0, scale="lin") == []

    def test_n_points_one_returns_f_min(self):
        assert sweep_frequencies(10, 1000, 1) == [10.0]
        assert sweep_frequencies(10, 1000, 1, scale="lin") == [10.0]

    def test_lin_two_points(self):
        got = sweep_frequencies(10, 20, 2, scale="lin")
        assert got == [10.0, 20.0]

    def test_lin_three_points(self):
        got = sweep_frequencies(0, 100, 3, scale="lin")
        assert len(got) == 3
        assert got[0] == 0.0
        assert got[-1] == 100.0
        assert got[1] == pytest.approx(50.0)

    def test_log_two_points(self):
        got = sweep_frequencies(10, 100, 2, scale="log")
        assert len(got) == 2
        assert got[0] == pytest.approx(10.0)
        assert got[1] == pytest.approx(100.0)

    def test_log_three_points_geometric(self):
        got = sweep_frequencies(10, 1000, 3, scale="log")
        assert len(got) == 3
        assert got[0] == pytest.approx(10.0)
        assert got[2] == pytest.approx(1000.0)
        # 10 * (1000/10)^0.5 = 100
        assert got[1] == pytest.approx(100.0)

    def test_log_f_min_zero_returns_empty(self):
        assert sweep_frequencies(0, 100, 5, scale="log") == []

    def test_log_f_max_zero_returns_empty(self):
        assert sweep_frequencies(10, 0, 5, scale="log") == []
