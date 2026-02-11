"""
Détecteur multimètre OWON (SCPI *IDN?, réponse OWON/XDM).
"""
from typing import List, Optional

import serial

from ..app_logger import get_logger
from .result import SerialDetectionResult

logger = get_logger(__name__)

OWON_BAUDS = [115200]
TIMEOUT = 0.5
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1


def _log(log_lines: List[str], msg: str) -> None:
    log_lines.append(msg)
    if msg.strip():
        logger.debug("détection: %s", msg)


def detect_owon(ports: List[str], log_lines: Optional[List[str]] = None) -> Optional[SerialDetectionResult]:
    """
    Cherche un multimètre OWON sur la liste de ports (premier trouvé).
    Remplit log_lines si fourni. Retourne SerialDetectionResult si trouvé, None sinon.
    """
    if log_lines is None:
        log_lines = []
    for port in ports:
        ok, baud = _try_owon_on_port(port, log_lines)
        if ok and baud is not None:
            logger.info("Multimètre OWON détecté sur %s à %s bauds", port, baud)
            _log(log_lines, f"# Multimètre trouvé sur {port} à {baud} bauds.")
            return SerialDetectionResult(port=port, baudrate=baud)
    return None


def _try_owon_on_port(port: str, log_lines: List[str]) -> tuple[bool, Optional[int]]:
    """Teste si un port répond en SCPI *IDN? et contient OWON ou XDM."""
    for baud in OWON_BAUDS:
        _log(log_lines, f"{port} [OWON] Ouverture {baud} bauds...")
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
                return (True, baud)
            _log(log_lines, f"{port} [OWON] Identifié: non")
        except Exception as e:
            _log(log_lines, f"{port} [OWON] Erreur: {e}")
            try:
                ser.close()
            except Exception:
                pass
    return (False, None)
