"""
Détection des équipements du banc (OWON, FY6900, RS305P, etc.).
API principale : run_detection(), update_config_from_detection().
"""
from .result import (
    BenchDetectionResult,
    SerialDetectionResult,
    UsbDetectionResult,
)
from .runner import run_detection, list_serial_ports
from .config_update import update_config_from_detection
from .owon import detect_owon
from .fy6900 import detect_fy6900
from .rs305p import detect_rs305p

__all__ = [
    "BenchDetectionResult",
    "SerialDetectionResult",
    "UsbDetectionResult",
    "run_detection",
    "list_serial_ports",
    "update_config_from_detection",
    "detect_owon",
    "detect_fy6900",
    "detect_rs305p",
]
