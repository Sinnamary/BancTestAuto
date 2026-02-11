"""
Mise à jour de la configuration à partir du résultat de détection.
Retourne une copie de config ; ne modifie pas le fichier.
"""
from typing import Any, Dict

from ..equipment import EquipmentKind, equipment_config_key
from .result import BenchDetectionResult, SerialDetectionResult, UsbDetectionResult


def update_config_from_detection(config: dict, detection_result: BenchDetectionResult) -> dict:
    """
    Retourne une copie de config avec les sections serial_* et usb_oscilloscope
    mises à jour selon les résultats de détection (port, baudrate, vendor_id, product_id).
    """
    out: Dict[str, Any] = dict(config)
    for kind, result in detection_result.results.items():
        key = equipment_config_key(kind)
        if not key:
            continue
        if key not in out:
            out[key] = {}
        else:
            out[key] = dict(out[key])
        if isinstance(result, SerialDetectionResult):
            if result.port is not None:
                out[key]["port"] = result.port
            if result.baudrate is not None:
                out[key]["baudrate"] = result.baudrate
        elif isinstance(result, UsbDetectionResult):
            if result.vendor_id is not None:
                out[key]["vendor_id"] = result.vendor_id
            if result.product_id is not None:
                out[key]["product_id"] = result.product_id
    return out
