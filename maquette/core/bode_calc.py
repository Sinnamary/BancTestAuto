"""
Stub bode_calc pour la maquette.
"""

def gain_linear(ue: float, us: float) -> float:
    return 0.0 if ue == 0 else us / ue

def gain_db(ue: float, us: float) -> float:
    return -100.0
