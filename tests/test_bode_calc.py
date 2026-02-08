"""
Tests du module core.bode_calc : gain linéaire et gain dB.
"""
import pytest

from core.bode_calc import gain_linear, gain_db


class TestGainLinear:
    def test_normal(self):
        assert gain_linear(2.0, 1.0) == 2.0
        assert gain_linear(0.5, 1.0) == 0.5

    def test_negative_gain(self):
        assert gain_linear(-2.0, 1.0) == -2.0

    def test_ue_zero_returns_zero(self):
        assert gain_linear(1.0, 0.0) == 0.0


class TestGainDb:
    def test_normal(self):
        # 20*log10(1) = 0
        assert gain_db(1.0, 1.0) == pytest.approx(0.0)
        # 20*log10(0.5) ≈ -6.02
        assert gain_db(0.5, 1.0) == pytest.approx(-6.020599913279624)

    def test_us_zero_returns_floor(self):
        assert gain_db(0.0, 1.0) == -200.0

    def test_ue_zero_linear_zero_then_floor(self):
        assert gain_linear(1.0, 0.0) == 0.0
        assert gain_db(1.0, 0.0) == -200.0

    def test_negative_us_returns_floor(self):
        """Si Us <= 0, gain dB retourne -200 (évite -inf)."""
        assert gain_db(-1.0, 1.0) == -200.0
