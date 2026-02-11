"""
Coordinateur de détection : exécute les détecteurs par type d'équipement,
en excluant les ports déjà attribués. Retourne un BenchDetectionResult.
"""
from typing import List, Optional

import serial.tools.list_ports

from ..app_logger import get_logger
from ..equipment import EquipmentKind, bench_equipment_kinds
from .result import BenchDetectionResult, SerialDetectionResult
from .owon import detect_owon
from .fy6900 import detect_fy6900
from .rs305p import detect_rs305p

logger = get_logger(__name__)


def list_serial_ports() -> List[str]:
    """Liste des ports série disponibles."""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def run_detection(
    kinds: Optional[List[EquipmentKind]] = None,
    log_lines: Optional[List[str]] = None,
) -> BenchDetectionResult:
    """
    Lance la détection pour les types d'équipement demandés.
    Un port attribué à un équipement n'est plus proposé aux suivants.
    kinds : liste des types à détecter (défaut : tous les équipements série du banc).
    log_lines : liste à remplir avec le log (créée si None).
    """
    if kinds is None:
        kinds = [EquipmentKind.MULTIMETER, EquipmentKind.GENERATOR, EquipmentKind.POWER_SUPPLY]
    if log_lines is None:
        log_lines = []

    ports = list_serial_ports()
    logger.info("Détection équipements — ports trouvés: %s", ports)
    log_lines.append("# Détection démarrée")
    log_lines.append(f"# Ports à scanner: {ports}")
    log_lines.append(f"# Équipements demandés: {[k.value for k in kinds]}")

    results: dict = {}
    used_ports: List[str] = []

    for kind in kinds:
        available = [p for p in ports if p not in used_ports]
        if not available:
            log_lines.append(f"# {kind.value}: aucun port restant.")
            continue
        log_lines.append("")
        log_lines.append(f"# Phase — {kind.value} (ports: {available})")

        if kind == EquipmentKind.MULTIMETER:
            r = detect_owon(available, log_lines)
        elif kind == EquipmentKind.GENERATOR:
            r = detect_fy6900(available, log_lines)
        elif kind == EquipmentKind.POWER_SUPPLY:
            r = detect_rs305p(available, log_lines)
        elif kind == EquipmentKind.OSCILLOSCOPE:
            r = _detect_oscilloscope_usb(log_lines)
        else:
            r = None

        if r is not None:
            results[kind] = r
            if isinstance(r, SerialDetectionResult) and r.port:
                used_ports.append(r.port)

    log_lines.append("")
    log_lines.append("# Détection terminée")
    return BenchDetectionResult(results=results, log_lines=log_lines)


def _detect_oscilloscope_usb(log_lines: List[str]) -> None:
    """
    Détection oscilloscope USB : pour l'instant pas d'auto-détection (liste USB
    possible via dos1102_usb_connection.list_usb_devices()). Retourne None.
    """
    log_lines.append("# Oscilloscope USB : non implémenté (config manuelle)")
    return None
