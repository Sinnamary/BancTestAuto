"""
Détecteur multimètre OWON (SCPI *IDN?, réponse OWON/XDM).
"""
from typing import List, Optional, Set

import serial
from serial import SerialException

from ..app_logger import get_logger
from .result import SerialDetectionResult

logger = get_logger(__name__)


def _is_port_open_error(exc: BaseException) -> bool:
    """True si l'exception indique une erreur grave d'ouverture de port (timeout, accès refusé)."""
    if isinstance(exc, (SerialException, OSError)):
        return True
    msg = str(exc).lower()
    return "could not open" in msg or "timeout" in msg or "sémaphore" in msg or "accès refusé" in msg or "permission" in msg

OWON_BAUDS = [115200]
TIMEOUT = 0.5
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1


def _log(log_lines: List[str], msg: str) -> None:
    log_lines.append(msg)
    if msg.strip():
        logger.debug("détection: %s", msg)


def detect_owon(
    ports: List[str],
    log_lines: Optional[List[str]] = None,
    unusable_ports: Optional[Set[str]] = None,
) -> Optional[SerialDetectionResult]:
    """
    Cherche un multimètre OWON sur la liste de ports (premier trouvé).
    Remplit log_lines si fourni. Les ports en erreur grave sont ajoutés à unusable_ports.
    """
    if log_lines is None:
        log_lines = []
    logger.debug("detect_owon: début — %d port(s) à tester: %s", len(ports), ports)
    for i, port in enumerate(ports):
        logger.debug("detect_owon: test port %d/%d — %s", i + 1, len(ports), port)
        ok, baud = _try_owon_on_port(port, log_lines, unusable_ports=unusable_ports)
        if ok and baud is not None:
            logger.info("Multimètre OWON détecté sur %s à %s bauds", port, baud)
            _log(log_lines, f"# Multimètre trouvé sur {port} à {baud} bauds.")
            logger.debug("detect_owon: trouvé sur %s @ %s bauds", port, baud)
            return SerialDetectionResult(port=port, baudrate=baud)
        logger.debug("detect_owon: %s non OWON, passage au port suivant", port)
    logger.debug("detect_owon: fin — aucun multimètre OWON trouvé")
    return None


def _try_owon_on_port(port: str, log_lines: List[str]) -> tuple[bool, Optional[int]]:
    """Teste si un port répond en SCPI *IDN? et contient OWON ou XDM."""
    logger.debug("_try_owon_on_port: %s — débits à tester: %s", port, OWON_BAUDS)
    for baud in OWON_BAUDS:
        _log(log_lines, f"{port} [OWON] Ouverture {baud} bauds...")
        logger.debug("_try_owon_on_port: %s ouverture @ %s bauds", port, baud)
        try:
            ser = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
                timeout=TIMEOUT,
                write_timeout=TIMEOUT,
            )
            _log(log_lines, f"{port} [OWON] TX *IDN?")
            ser.write(b"*IDN?\n")
            raw = ser.readline()
            rx_str = raw.decode("utf-8", errors="replace").strip() if raw else ""
            if rx_str:
                _log(log_lines, f"{port} [OWON] RX {rx_str!r}")
            ser.close()
            _log(log_lines, f"{port} [OWON] Fermeture.")
            if rx_str and ("OWON" in rx_str.upper() or "XDM" in rx_str.upper()):
                _log(log_lines, f"{port} [OWON] Identifié: oui")
                logger.debug("_try_owon_on_port: %s réponse OWON/XDM reçue: %r", port, rx_str[:80])
                return (True, baud)
            _log(log_lines, f"{port} [OWON] Identifié: non")
            logger.debug("_try_owon_on_port: %s réponse invalide ou vide: %r", port, rx_str[:80] if rx_str else "(vide)")
        except Exception as e:
            _log(log_lines, f"{port} [OWON] Erreur: {e}")
            logger.debug("_try_owon_on_port: %s exception — %s", port, e, exc_info=True)
            try:
                ser.close()
            except Exception:
                pass
    return (False, None)
