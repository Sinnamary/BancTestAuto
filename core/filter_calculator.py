"""
Calcul des fréquences de coupure pour les principaux types de filtres passifs.
Formules basées sur R (résistance, Ω), L (inductance, H), C (capacité, F).
"""
import math

PI_2 = 2.0 * math.pi


def rc_passe_bas_fc(r_ohm: float, c_farad: float) -> float | None:
    """Filtre RC passe-bas : fc = 1 / (2π R C)."""
    if r_ohm <= 0 or c_farad <= 0:
        return None
    return 1.0 / (PI_2 * r_ohm * c_farad)


def rc_passe_haut_fc(r_ohm: float, c_farad: float) -> float | None:
    """Filtre RC passe-haut (CR) : fc = 1 / (2π R C)."""
    return rc_passe_bas_fc(r_ohm, c_farad)


def pont_wien_fc(r_ohm: float, c_farad: float) -> float | None:
    """Pont de Wien (symétrique R1=R2=R, C1=C2=C) : fc = 1 / (2π R C)."""
    return rc_passe_bas_fc(r_ohm, c_farad)


def pont_wien_fc_general(
    r1_ohm: float, r2_ohm: float, c1_farad: float, c2_farad: float
) -> float | None:
    """Pont de Wien général : fc = 1 / (2π √(R1 R2 C1 C2))."""
    if r1_ohm <= 0 or r2_ohm <= 0 or c1_farad <= 0 or c2_farad <= 0:
        return None
    return 1.0 / (PI_2 * math.sqrt(r1_ohm * r2_ohm * c1_farad * c2_farad))


def rlc_resonance_fc(r_ohm: float, l_henry: float, c_farad: float) -> float | None:
    """Filtre RLC : fréquence de résonance f0 = 1 / (2π √(L C)). R n'intervient pas."""
    if l_henry <= 0 or c_farad <= 0:
        return None
    return 1.0 / (PI_2 * math.sqrt(l_henry * c_farad))


def rlc_quality_factor(r_ohm: float, l_henry: float, c_farad: float) -> float | None:
    """Facteur de qualité série RLC : Q = (1/R) √(L/C)."""
    if r_ohm <= 0 or l_henry <= 0 or c_farad <= 0:
        return None
    return math.sqrt(l_henry / c_farad) / r_ohm


def double_t_fc(r_ohm: float, c_farad: float) -> float | None:
    """Filtre Double T (Twin-T) symétrique : fréquence de rejet fc = 1 / (2π R C)."""
    return rc_passe_bas_fc(r_ohm, c_farad)
