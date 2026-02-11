"""
Détection automatique : façade vers core.detection.
Conserve l'API historique (detect_devices, update_config_ports) pour compatibilité
avec MainWindow et DetectionWorker. La logique est dans core.detection.

REMOVE_AFTER_PHASE5: Façade de compatibilité. Une fois l'UI migrée vers core.detection
et ConnectionController, supprimer ce module et remplacer les appels par
core.detection.run_detection, update_config_from_detection, list_serial_ports.
Voir docs/EVOLUTION_4_EQUIPEMENTS.md.
"""
from typing import Optional

from .app_logger import get_logger
from .equipment import EquipmentKind
from .detection import run_detection, update_config_from_detection

logger = get_logger(__name__)


def list_serial_ports() -> list[str]:
    """Retourne la liste des ports série disponibles (délègue à core.detection)."""
    from .detection import list_serial_ports as _list
    return _list()


def detect_devices() -> tuple[Optional[str], Optional[int], Optional[str], Optional[int], list[str]]:
    """
    Détection multimètre OWON et générateur FY6900.
    Retourne (port_multimetre, baud_multimetre, port_generateur, baud_generateur, log_detaille).
    Délègue à core.detection.run_detection pour les 2 premiers équipements.
    """
    result = run_detection(
        kinds=[EquipmentKind.MULTIMETER, EquipmentKind.GENERATOR],
        log_lines=[],
    )
    m = result.get_serial(EquipmentKind.MULTIMETER)
    g = result.get_serial(EquipmentKind.GENERATOR)
    multimeter_port = m.port if m else None
    multimeter_baud = m.baudrate if m else None
    generator_port = g.port if g else None
    generator_baud = g.baudrate if g else None
    logger.info("Détection terminée — multimètre=%s@%s, générateur=%s@%s", multimeter_port, multimeter_baud, generator_port, generator_baud)
    return (multimeter_port, multimeter_baud, generator_port, generator_baud, result.log_lines)


def update_config_ports(
    config: dict,
    multimeter_port: Optional[str],
    generator_port: Optional[str],
    multimeter_baud: Optional[int] = None,
    generator_baud: Optional[int] = None,
) -> dict:
    """
    Retourne une copie de config avec serial_multimeter/generator.port et .baudrate
    mis à jour. Délègue à core.detection.update_config_from_detection.
    """
    from .detection.result import BenchDetectionResult, SerialDetectionResult
    results = {}
    if multimeter_port is not None:
        results[EquipmentKind.MULTIMETER] = SerialDetectionResult(port=multimeter_port, baudrate=multimeter_baud)
    if generator_port is not None:
        results[EquipmentKind.GENERATOR] = SerialDetectionResult(port=generator_port, baudrate=generator_baud)
    dummy_result = BenchDetectionResult(results=results, log_lines=[])
    return update_config_from_detection(config, dummy_result)
