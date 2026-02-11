"""Tests du calcul de cutoff (-3 dB, etc.)."""
import pytest

from ui.bode_csv_viewer.model import BodeCsvPoint, BodeCsvDataset
from ui.bode_csv_viewer.cutoff import Cutoff3DbFinder, CutoffResult


class TestCutoffResult:
    def test_fields(self):
        r = CutoffResult(fc_hz=1000.0, gain_db=-3.0)
        assert r.fc_hz == 1000.0
        assert r.gain_db == -3.0


class TestCutoff3DbFinder:
    def _dataset(self, freqs, gains_db):
        pts = [
            BodeCsvPoint(f, 1.0, 10 ** (g / 20.0), g)
            for f, g in zip(freqs, gains_db)
        ]
        return BodeCsvDataset(pts)

    def test_find_first_cutoff(self):
        ds = self._dataset([10, 100, 500, 1000], [0, -1, -3.5, -10])
        finder = Cutoff3DbFinder()
        r = finder.find(ds)
        assert r is not None
        assert 100 < r.fc_hz < 1000
        assert r.gain_db == pytest.approx(-3.0)

    def test_find_all_single_cutoff(self):
        ds = self._dataset([10, 100, 1000], [0, -1.5, -6])
        finder = Cutoff3DbFinder()
        all_r = finder.find_all(ds)
        assert len(all_r) == 1
        assert all_r[0].gain_db == pytest.approx(-3.0)

    def test_find_all_band_stop_two_cutoffs(self):
        # Courbe qui descend, remonte, redescend : 2 croisements -3 dB
        freqs = [10, 100, 500, 1000, 2000, 5000]
        gains = [0, -2, -5, -2, -5, -10]
        ds = self._dataset(freqs, gains)
        finder = Cutoff3DbFinder()
        all_r = finder.find_all(ds, gain_ref=0)
        assert len(all_r) >= 2

    def test_find_empty_dataset(self):
        finder = Cutoff3DbFinder()
        assert finder.find(BodeCsvDataset([])) is None
        assert finder.find_all(BodeCsvDataset([])) == []

    def test_find_crossings_at_gain(self):
        ds = self._dataset([10, 100, 1000], [0, -6, -20])
        finder = Cutoff3DbFinder()
        r = finder.find_crossings_at_gain(ds, -6.0)
        assert len(r) >= 1
        assert 10 <= r[0].fc_hz <= 1000
        assert r[0].gain_db == pytest.approx(-6.0)

    def test_find_crossings_at_gain_multiple(self):
        freqs = [10, 50, 100, 200, 500]
        gains = [0, -2, -5, -2, -4]
        ds = self._dataset(freqs, gains)
        finder = Cutoff3DbFinder()
        r = finder.find_crossings_at_gain(ds, -3.0)
        assert len(r) >= 1
