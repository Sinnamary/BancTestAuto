"""
Stub détection pour la maquette : pas de scan des ports.
"""
from typing import Optional

def list_serial_ports() -> list[str]:
    return []


def detect_devices() -> tuple[Optional[str], Optional[int], Optional[str], Optional[int], list[str]]:
    return (None, None, None, None, [])


def update_config_ports(
    config: dict,
    multimeter_port: Optional[str],
    generator_port: Optional[str],
    multimeter_baud: Optional[int] = None,
    generator_baud: Optional[int] = None,
) -> dict:
    """Retourne une copie de config (en maquette on ne modifie pas vraiment)."""
    import copy
    out = copy.deepcopy(config)
    if multimeter_port is not None and "serial_multimeter" in out:
        out["serial_multimeter"] = dict(out["serial_multimeter"], port=multimeter_port)
        if multimeter_baud is not None:
            out["serial_multimeter"]["baudrate"] = multimeter_baud
    if generator_port is not None and "serial_generator" in out:
        out["serial_generator"] = dict(out["serial_generator"], port=generator_port)
        if generator_baud is not None:
            out["serial_generator"]["baudrate"] = generator_baud
    return out
