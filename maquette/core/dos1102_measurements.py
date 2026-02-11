"""
Stub formatage mesures DOS1102 pour la maquette.
"""
from . import dos1102_commands as CMD


def format_meas_general_response(raw: str | bytes) -> str:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return "—"
    return str(raw).strip() or "—"


def format_measurements_text(measurements: dict[str, str], add_bode_hint: bool = False) -> str:
    lines = [f"{k}: {v}" for k, v in measurements.items()]
    if add_bode_hint:
        lines.append("")
        lines.append("(Phase Bode : φ = 360° × délai / période)")
    return "\n".join(lines)


def get_measure_types_per_channel():
    return list(CMD.MEAS_TYPES_PER_CHANNEL)


def get_measure_types_inter_channel():
    return list(CMD.MEAS_TYPES_INTER_CHANNEL)
