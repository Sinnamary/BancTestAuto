"""
Tests de core.filter_test : BodePoint, FilterTestConfig, FilterTest (orchestration avec mocks).
"""
from unittest.mock import MagicMock

import pytest

from core.filter_test import BodePoint, FilterTest, FilterTestConfig


class TestBodePoint:
    def test_dataclass_fields(self):
        p = BodePoint(f_hz=100.0, us_v=0.5, gain_linear=0.5, gain_db=-6.02)
        assert p.f_hz == 100.0
        assert p.us_v == 0.5
        assert p.gain_linear == 0.5
        assert p.gain_db == pytest.approx(-6.02)


class TestFilterTestConfig:
    def test_dataclass_fields(self):
        cfg = FilterTestConfig(
            generator_channel=1,
            f_min_hz=10,
            f_max_hz=10000,
            n_points=20,
            scale="log",
            settling_ms=200,
            ue_rms=1.0,
        )
        assert cfg.scale == "log"
        assert cfg.ue_rms == 1.0


class TestFilterTest:
    def test_set_config(self):
        gen = MagicMock()
        meas = MagicMock()
        cfg = FilterTestConfig(1, 10, 100, 5, "log", 100, 1.0)
        ft = FilterTest(gen, meas, cfg)
        cfg2 = FilterTestConfig(1, 20, 200, 10, "lin", 50, 1.0)
        ft.set_config(cfg2)
        assert ft._config.f_min_hz == 20

    def test_abort_stops_sweep(self):
        gen = MagicMock()
        meas = MagicMock()
        meas.set_voltage_ac = MagicMock()
        meas.read_value = MagicMock(return_value="0.5")
        meas.parse_float = MagicMock(return_value=0.5)
        cfg = FilterTestConfig(1, 10, 1000, 100, "log", 10, 1.0)  # 100 points
        ft = FilterTest(gen, meas, cfg)
        points_seen = []

        def on_point(p, i, t):
            points_seen.append(p)
            if len(points_seen) >= 2:
                ft.abort()

        result = ft.run_sweep(on_point=on_point)
        assert len(result) >= 1
        assert len(result) < 100
        gen.set_output.assert_called_with(False)

    def test_run_sweep_returns_bode_points(self):
        gen = MagicMock()
        meas = MagicMock()
        meas.set_voltage_ac = MagicMock()
        meas.read_value = MagicMock(return_value="0.707")
        meas.parse_float = MagicMock(return_value=0.707)
        cfg = FilterTestConfig(1, 10, 100, 3, "lin", 5, 1.0)
        ft = FilterTest(gen, meas, cfg)
        results = ft.run_sweep()
        assert len(results) == 3
        for p in results:
            assert isinstance(p, BodePoint)
            assert p.f_hz >= 10
            assert p.us_v == 0.707
        gen.set_output.assert_called_with(False)
