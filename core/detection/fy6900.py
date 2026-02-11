"""
Détecteur générateur FeelTech FY6900 (commande WMW00 + LF, réponse non SCPI).
"""
from typing import List, Optional

import serial

from ..app_logger import get_logger
from .result import SerialDetectionResult

logger = get_logger(__name__)

FY6900_BAUD = 115200
TIMEOUT = 0.5
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1


def _log(log_lines: List[str], msg: str) -> None:
    log_lines.append(msg)
    if msg.strip():
        logger.debug("détection: %s", msg)


def detect_fy6900(ports: List[str], log_lines: Optional[List[str]] = None) -> Optional[SerialDetectionResult]:
    """
    Cherche un générateur FY6900 sur la liste de ports (premier trouvé).
    Rejette les réponses SCPI (OWON/XDM). Remplit log_lines si fourni.
    """
    if log_lines is None:
        log_lines = []
    logger.debug("detect_fy6900: début — %d port(s) à tester: %s (baud=%s)", len(ports), ports, FY6900_BAUD)
    for i, port in enumerate(ports):
        logger.debug("detect_fy6900: test port %d/%d — %s", i + 1, len(ports), port)
        if _try_fy6900_on_port(port, log_lines):
            logger.info("Générateur FY6900 détecté sur %s", port)
            _log(log_lines, f"# Générateur trouvé sur {port}.")
            logger.debug("detect_fy6900: trouvé sur %s", port)
            return SerialDetectionResult(port=port, baudrate=FY6900_BAUD)
        logger.debug("detect_fy6900: %s non FY6900, passage au port suivant", port)
    logger.debug("detect_fy6900: fin — aucun générateur FY6900 trouvé")
    return None


def _try_fy6900_on_port(port: str, log_lines: List[str]) -> bool:
    """Teste si le port répond au protocole FY6900 (WMW00) sans réponse SCPI."""
    logger.debug("_try_fy6900_on_port: %s ouverture @ %s bauds", port, FY6900_BAUD)
    _log(log_lines, f"{port} [FY6900] Ouverture {FY6900_BAUD} bauds...")
    try:
        ser = serial.Serial(
            port=port,
            baudrate=FY6900_BAUD,
            bytesize=BYTESIZE,
            parity=PARITY,
            stopbits=STOPBITS,
            timeout=TIMEOUT,
            write_timeout=TIMEOUT,
        )
        _log(log_lines, f"{port} [FY6900] TX WMW00")
        ser.write(b"WMW00\n")
        data = ser.read(10)
        if data:
            rx_str = data.decode("utf-8", errors="replace").strip() or data.hex(" ")
            _log(log_lines, f"{port} [FY6900] RX {rx_str!r}")
        else:
            _log(log_lines, f"{port} [FY6900] RX (timeout ou vide)")
        ser.close()
        _log(log_lines, f"{port} [FY6900] Fermeture.")
        if not data:
            logger.debug("_try_fy6900_on_port: %s réponse vide ou timeout", port)
            return False
        decoded = data.decode("utf-8", errors="replace")
        logger.debug("_try_fy6900_on_port: %s données reçues (%d octets): %r", port, len(data), decoded[:50] if decoded else data.hex())
        if "OWON" in decoded.upper() or "XDM" in decoded.upper() or "*IDN" in decoded.upper():
            _log(log_lines, f"{port} [FY6900] Accepté: non (réponse SCPI)")
            logger.debug("_try_fy6900_on_port: %s rejeté (réponse type SCPI)", port)
            return False
        _log(log_lines, f"{port} [FY6900] Accepté: oui")
        logger.debug("_try_fy6900_on_port: %s accepté comme FY6900", port)
        return True
    except Exception as e:
        _log(log_lines, f"{port} [FY6900] Erreur: {e}")
        logger.debug("_try_fy6900_on_port: %s exception — %s", port, e, exc_info=True)
        try:
            ser.close()
        except Exception:
            pass
        return False
