"""Tests du modèle Bode (BodeCsvPoint, BodeCsvDataset)."""
import pytest

from ui.bode_csv_viewer.model import BodeCsvPoint, BodeCsvDataset


class TestBodeCsvPoint:
    """BodeCsvPoint : dataclass fréquence, tension, gain linéaire/dB."""

    def test_create(self):
        p = BodeCsvPoint(f_hz=100.0, us_v=1.0, gain_linear=0.5, gain_db=-6.02)
        assert p.f_hz == 100.0
        assert p.us_v == 1.0
        assert p.gain_linear == 0.5
        assert p.gain_db == pytest.approx(-6.02)

    def test_equality_by_value(self):
        a = BodeCsvPoint(10.0, 1.0, 1.0, 0.0)
        b = BodeCsvPoint(10.0, 1.0, 1.0, 0.0)
        assert a == b


class TestBodeCsvDataset:
    """BodeCsvDataset : conteneur de points, freqs_hz, gains_db, gains_linear."""

    def test_empty(self):
        ds = BodeCsvDataset([])
        assert ds.count == 0
        assert ds.is_empty() is True
        assert ds.points == []
        assert ds.freqs_hz() == []
        assert ds.gains_db() == []
        assert ds.gains_linear() == []

    def test_with_points(self):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
        ]
        ds = BodeCsvDataset(pts)
        assert ds.count == 2
        assert ds.is_empty() is False
        assert ds.freqs_hz() == [10.0, 100.0]
        assert ds.gains_db() == [0.0, -3.0]
        assert ds.gains_linear() == [1.0, 0.7]

    def test_points_copy(self):
        pts = [BodeCsvPoint(1.0, 1.0, 1.0, 0.0)]
        ds = BodeCsvDataset(pts)
        assert ds.points is not pts
        assert len(ds.points) == 1
