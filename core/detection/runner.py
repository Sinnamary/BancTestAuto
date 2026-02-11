"""
Coordinateur de détection : exécute les détecteurs par type d'équipement,
en excluant les ports déjà attribués et les ports en erreur grave (timeout, accès refusé).
Retourne un BenchDetectionResult.
"""
from typing import Callable, List, Optional, Set, Union

import serial.tools.list_ports

from ..app_logger import get_logger
from ..equipment import EquipmentKind, bench_equipment_kinds
from .result import BenchDetectionResult, SerialDetectionResult, UsbDetectionResult
from .owon import detect_owon
from .fy6900 import detect_fy6900
from .rs305p import detect_rs305p

logger = get_logger(__name__)

# Détecteurs série : (ports_disponibles, log_lines, unusable_ports) -> SerialDetectionResult | None
_SERIAL_DETECTORS: dict[EquipmentKind, Callable[..., Optional[SerialDetectionResult]]] = {
    EquipmentKind.MULTIMETER: detect_owon,
    EquipmentKind.GENERATOR: detect_fy6900,
    EquipmentKind.POWER_SUPPLY: detect_rs305p,
}


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

    logger.debug("run_detection: début — kinds=%s", [k.value for k in kinds])
    ports = list_serial_ports()
    logger.info("Détection équipements — ports trouvés: %s", ports)
    logger.debug("run_detection: %d port(s) série à scanner", len(ports))
    log_lines.append("# Détection démarrée")
    log_lines.append(f"# Ports à scanner: {ports}")
    log_lines.append(f"# Équipements demandés: {[k.value for k in kinds]}")

    results: dict = {}
    used_ports: List[str] = []
    unusable_ports: Set[str] = set()  # ports en erreur grave (timeout, accès refusé) — exclus des phases suivantes
    logger.debug("run_detection: used_ports initial = %s", used_ports)

    for kind in kinds:
        available = [p for p in ports if p not in used_ports and p not in unusable_ports]
        logger.debug("run_detection: phase %s — available=%s, used_ports=%s, unusable_ports=%s", kind.value, available, used_ports, unusable_ports)
        if kind != EquipmentKind.OSCILLOSCOPE and not available:
            log_lines.append(f"# {kind.value}: aucun port restant.")
            logger.debug("run_detection: phase %s ignorée (aucun port restant)", kind.value)
            continue
        log_lines.append("")
        if kind == EquipmentKind.OSCILLOSCOPE:
            log_lines.append("# Phase — oscilloscope (USB PyUSB)")
            logger.debug("run_detection: lancement détection oscilloscope USB")
        else:
            log_lines.append(f"# Phase — {kind.value} (ports: {available})")
            logger.debug("run_detection: lancement détection %s sur %d port(s)", kind.value, len(available))

        r = _run_detector_for_kind(kind, available, log_lines, unusable_ports)

        if r is not None:
            results[kind] = r
            if isinstance(r, SerialDetectionResult) and r.port:
                used_ports.append(r.port)
                logger.debug("run_detection: %s détecté — port=%s baud=%s, used_ports=%s", kind.value, r.port, r.baudrate, used_ports)
            elif isinstance(r, UsbDetectionResult):
                logger.debug("run_detection: %s détecté (USB) — VID=0x%04X PID=0x%04X", kind.value, r.vendor_id or 0, r.product_id or 0)
        else:
            logger.debug("run_detection: %s non détecté", kind.value)

    log_lines.append("")
    log_lines.append("# Détection terminée")
    logger.debug("run_detection: fin — results=%s, used_ports=%s", list(results.keys()), used_ports)
    return BenchDetectionResult(results=results, log_lines=log_lines)


def _run_detector_for_kind(
    kind: EquipmentKind,
    available: List[str],
    log_lines: List[str],
    unusable_ports: Set[str],
) -> Optional[Union[SerialDetectionResult, UsbDetectionResult]]:
    """Délègue au détecteur approprié (série ou USB). Réutilisable et réduit la complexité cyclomatique."""
    if kind == EquipmentKind.OSCILLOSCOPE:
        return _detect_oscilloscope_usb(log_lines)
    detector = _SERIAL_DETECTORS.get(kind)
    if detector is not None:
        return detector(available, log_lines, unusable_ports=unusable_ports)
    return None


# Mots-clés pour identifier un oscilloscope USB (nom produit ou description)
OSCILLOSCOPE_USB_KEYWORDS = ("oscilloscope", "oscillo", "dos1102", "hanmatek", "dso")


def _detect_oscilloscope_usb(log_lines: List[str]) -> Optional[UsbDetectionResult]:
    """
    Détection oscilloscope USB via PyUSB : liste les périphériques USB et retient
    le premier dont la description contient un mot-clé (oscilloscope, DOS1102, Hanmatek, etc.).
    Retourne UsbDetectionResult(vendor_id, product_id) si trouvé, None sinon.
    """
    logger.debug("_detect_oscilloscope_usb: début")
    try:
        from ..dos1102_usb_connection import list_usb_devices
    except ImportError as e:
        log_lines.append("# PyUSB non disponible (pip install pyusb)")
        logger.debug("Oscilloscope USB: import list_usb_devices impossible — %s", e)
        return None

    devices = list_usb_devices()
    log_lines.append(f"# Périphériques USB trouvés: {len(devices)}")
    logger.debug("_detect_oscilloscope_usb: %d périphérique(s) USB, mots-clés=%s", len(devices), OSCILLOSCOPE_USB_KEYWORDS)
    for vid, pid, desc in devices:
        log_lines.append(f"#   {desc} (VID=0x{vid:04X}, PID=0x{pid:04X})")
        desc_lower = desc.lower()
        matched = [kw for kw in OSCILLOSCOPE_USB_KEYWORDS if kw in desc_lower]
        logger.debug("_detect_oscilloscope_usb: périphérique %s — desc_lower=%r, mots-clés trouvés=%s", f"0x{vid:04X}:0x{pid:04X}", desc_lower, matched or "aucun")
        if matched:
            log_lines.append(f"# Oscilloscope identifié: {desc}")
            logger.info("Oscilloscope USB détecté: %s (VID=0x%04X, PID=0x%04X)", desc, vid, pid)
            logger.debug("_detect_oscilloscope_usb: retour UsbDetectionResult(0x%04X, 0x%04X)", vid, pid)
            return UsbDetectionResult(vendor_id=vid, product_id=pid)

    log_lines.append("# Aucun périphérique USB ne correspond (mots-clés: " + ", ".join(OSCILLOSCOPE_USB_KEYWORDS) + ")")
    logger.debug("_detect_oscilloscope_usb: aucun oscilloscope trouvé")
    return None
