"""
Tests de core.filter_test : BodePoint, FilterTestConfig, FilterTest (orchestration avec mocks).
"""
from unittest.mock import MagicMock

import pytest

from core.bode_measure_source import MultimeterBodeAdapter
from core.filter_test import BodePoint, FilterTest, FilterTestConfig


class TestBodePoint:
    def test_dataclass_fields(self):
        p = BodePoint(f_hz=100.0, us_v=0.5, gain_linear=0.5, gain_db=-6.02)
        assert p.f_hz == 100.0
        assert p.us_v == 0.5
        assert p.gain_linear == 0.5
        assert p.gain_db == pytest.approx(-6.02)

    def test_bode_point_phase_optional(self):
        p = BodePoint(f_hz=100.0, us_v=0.5, gain_linear=0.5, gain_db=-6.02, phase_deg=-45.0)
        assert p.phase_deg == -45.0
        p2 = BodePoint(f_hz=100.0, us_v=0.5, gain_linear=0.5, gain_db=-6.02)
        assert p2.phase_deg is None


class TestFilterTestConfig:
    def test_dataclass_fields(self):
        cfg = FilterTestConfig(
            generator_channel=1,
            f_min_hz=10,
            f_max_hz=10000,
            points_per_decade=10,
            scale="log",
            settling_ms=200,
            ue_rms=1.0,
        )
        assert cfg.scale == "log"
        assert cfg.ue_rms == 1.0
        assert cfg.points_per_decade == 10


def _make_meter_adapter():
    """Construit un adaptateur multimètre mock pour FilterTest."""
    meas = MagicMock()
    meas.set_voltage_ac = MagicMock()
    meas.read_value = MagicMock(return_value="0.5")
    meas.parse_float = MagicMock(return_value=0.5)
    return MultimeterBodeAdapter(meas)


class TestFilterTest:
    def test_set_config(self):
        gen = MagicMock()
        cfg = FilterTestConfig(1, 10, 100, 5, "log", 100, 1.0)
        ft = FilterTest(gen, _make_meter_adapter(), cfg)
        cfg2 = FilterTestConfig(1, 20, 200, 10, "lin", 50, 1.0)
        ft.set_config(cfg2)
        assert ft._config.f_min_hz == 20

    def test_abort_stops_sweep(self):
        gen = MagicMock()
        adapter = _make_meter_adapter()
        cfg = FilterTestConfig(1, 10, 1000, 50, "log", 10, 1.0)  # 50 pts/décade × 2 décades ≈ 100 points
        ft = FilterTest(gen, adapter, cfg)
        points_seen = []

        def on_point(p, i, t):
            points_seen.append(p)
            if len(points_seen) >= 2:
                ft.abort()

        result = ft.run_sweep(on_point=on_point)
        assert len(result) >= 1
        assert len(result) < 100
        gen.set_output.assert_called_with(False, channel=1)

    def test_run_sweep_returns_bode_points(self):
        gen = MagicMock()
        adapter = _make_meter_adapter()
        adapter._measurement.read_value = MagicMock(return_value="0.707")
        adapter._measurement.parse_float = MagicMock(return_value=0.707)
        cfg = FilterTestConfig(1, 10, 100, 3, "lin", 5, 1.0)  # 3 pts/décade × 1 décade = 3 points
        ft = FilterTest(gen, adapter, cfg)
        results = ft.run_sweep()
        assert len(results) >= 2 and len(results) <= 4  # après arrondi fréquences rondes, déduplication
        for p in results:
            assert isinstance(p, BodePoint)
            assert p.f_hz >= 10
            assert p.us_v == 0.707
            assert p.phase_deg is None
        gen.set_output.assert_called_with(False, channel=1)

    def test_run_sweep_when_parse_float_returns_none_uses_zero(self):
        """Si parse_float retourne None, us = 0.0 puis gain calculé (couverture ligne 101)."""
        gen = MagicMock()
        adapter = _make_meter_adapter()
        adapter._measurement.read_value = MagicMock(return_value="OVLD")
        adapter._measurement.parse_float = MagicMock(return_value=None)
        cfg = FilterTestConfig(1, 10, 100, 2, "lin", 5, 1.0)  # 2 points
        ft = FilterTest(gen, adapter, cfg)
        results = ft.run_sweep()
        assert len(results) >= 1 and len(results) <= 3
        for p in results:
            assert p.us_v == 0.0
            assert p.gain_linear == 0.0
            assert p.gain_db == -200.0

    def test_run_sweep_calls_on_progress(self):
        """run_sweep(on_progress=...) appelle on_progress à chaque point (couverture 109)."""
        gen = MagicMock()
        adapter = _make_meter_adapter()
        cfg = FilterTestConfig(1, 10, 100, 3, "lin", 5, 1.0)  # 3 points
        ft = FilterTest(gen, adapter, cfg)
        progress_calls = []

        def on_progress(done, total):
            progress_calls.append((done, total))

        ft.run_sweep(on_progress=on_progress)
        assert len(progress_calls) >= 2
        assert progress_calls[-1][0] == progress_calls[-1][1]  # (done, total) avec done == total à la fin
