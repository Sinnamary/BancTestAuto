"""
Tests du module core.filter_calculator : formules de fréquence de coupure (sans UI).
"""
import math

import pytest

from core.filter_calculator import (
    PI_2,
    rc_passe_bas_fc,
    rc_passe_haut_fc,
    pont_wien_fc,
    rlc_resonance_fc,
    double_t_fc,
)


class TestFilterCalculatorConstants:
    def test_pi_2(self):
        assert PI_2 == pytest.approx(2.0 * math.pi)


class TestRcPasseBasFc:
    def test_formula_fc(self):
        # fc = 1 / (2π R C) ; R=1kΩ, C=1µF → fc ≈ 159.15 Hz
        r, c = 1000.0, 1e-6
        fc = rc_passe_bas_fc(r, c)
        assert fc is not None
        assert fc == pytest.approx(1.0 / (2 * math.pi * r * c), rel=1e-9)
        assert fc == pytest.approx(159.1549, rel=1e-3)

    def test_r_negative_returns_none(self):
        assert rc_passe_bas_fc(-1, 1e-6) is None
        assert rc_passe_bas_fc(0, 1e-6) is None

    def test_c_negative_returns_none(self):
        assert rc_passe_bas_fc(1000, -1) is None
        assert rc_passe_bas_fc(1000, 0) is None

    def test_typical_values(self):
        # R=10k, C=100nF → fc ≈ 159.15 Hz
        fc = rc_passe_bas_fc(10e3, 100e-9)
        assert fc == pytest.approx(159.15, rel=1e-2)


class TestRcPasseHautFc:
    def test_same_as_passe_bas(self):
        r, c = 1000.0, 1e-6
        assert rc_passe_haut_fc(r, c) == rc_passe_bas_fc(r, c)

    def test_invalid_returns_none(self):
        assert rc_passe_haut_fc(0, 1e-6) is None


class TestPontWienFc:
    def test_same_as_rc_passe_bas(self):
        r, c = 2200.0, 10e-9
        assert pont_wien_fc(r, c) == rc_passe_bas_fc(r, c)

    def test_typical(self):
        fc = pont_wien_fc(10e3, 10e-9)
        assert fc is not None
        assert fc == pytest.approx(1591.55, rel=1e-2)


class TestRlcResonanceFc:
    def test_formula_f0(self):
        # f0 = 1 / (2π √(L C)) ; R n'intervient pas
        l_h, c_f = 1e-3, 1e-6
        fc = rlc_resonance_fc(100.0, l_h, c_f)
        assert fc is not None
        expected = 1.0 / (2 * math.pi * math.sqrt(l_h * c_f))
        assert fc == pytest.approx(expected, rel=1e-9)
        assert fc == pytest.approx(5032.9, rel=1e-2)

    def test_l_zero_returns_none(self):
        assert rlc_resonance_fc(100, 0, 1e-6) is None
        assert rlc_resonance_fc(100, -1e-3, 1e-6) is None

    def test_c_zero_returns_none(self):
        assert rlc_resonance_fc(100, 1e-3, 0) is None
        assert rlc_resonance_fc(100, 1e-3, -1e-6) is None

    def test_r_ignored(self):
        fc1 = rlc_resonance_fc(10, 1e-3, 1e-6)
        fc2 = rlc_resonance_fc(1e6, 1e-3, 1e-6)
        assert fc1 == fc2


class TestDoubleTFc:
    def test_same_as_rc_passe_bas(self):
        r, c = 4700.0, 22e-9
        assert double_t_fc(r, c) == rc_passe_bas_fc(r, c)

    def test_typical(self):
        fc = double_t_fc(10e3, 10e-9)
        assert fc == pytest.approx(1591.55, rel=1e-2)
