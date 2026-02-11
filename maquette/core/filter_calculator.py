"""
Calcul des fréquences de coupure (stub maquette = même logique pure que le projet).
"""
import math

PI_2 = 2.0 * math.pi


def rc_passe_bas_fc(r_ohm: float, c_farad: float) -> float | None:
    if r_ohm <= 0 or c_farad <= 0:
        return None
    return 1.0 / (PI_2 * r_ohm * c_farad)


def rc_passe_haut_fc(r_ohm: float, c_farad: float) -> float | None:
    return rc_passe_bas_fc(r_ohm, c_farad)


def pont_wien_fc(r_ohm: float, c_farad: float) -> float | None:
    return rc_passe_bas_fc(r_ohm, c_farad)


def pont_wien_fc_general(
    r1_ohm: float, r2_ohm: float, c1_farad: float, c2_farad: float
) -> float | None:
    if r1_ohm <= 0 or r2_ohm <= 0 or c1_farad <= 0 or c2_farad <= 0:
        return None
    return 1.0 / (PI_2 * math.sqrt(r1_ohm * r2_ohm * c1_farad * c2_farad))


def rlc_resonance_fc(r_ohm: float, l_henry: float, c_farad: float) -> float | None:
    if l_henry <= 0 or c_farad <= 0:
        return None
    return 1.0 / (PI_2 * math.sqrt(l_henry * c_farad))


def rlc_quality_factor(r_ohm: float, l_henry: float, c_farad: float) -> float | None:
    if r_ohm <= 0 or l_henry <= 0 or c_farad <= 0:
        return None
    return math.sqrt(l_henry / c_farad) / r_ohm


def double_t_fc(r_ohm: float, c_farad: float) -> float | None:
    return rc_passe_bas_fc(r_ohm, c_farad)
