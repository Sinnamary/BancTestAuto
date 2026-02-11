"""
Détecteur alimentation RS305P (Modbus RTU, 9600 baud, lecture registre).
"""
from typing import List, Optional, Set

import serial
from serial import SerialException

from ..app_logger import get_logger
from .result import SerialDetectionResult

logger = get_logger(__name__)


def _is_port_open_error(exc: BaseException) -> bool:
    """True si l'exception indique une erreur grave d'ouverture de port."""
    if isinstance(exc, (SerialException, OSError)):
        return True
    msg = str(exc).lower()
    return "could not open" in msg or "timeout" in msg or "sémaphore" in msg or "accès refusé" in msg or "permission" in msg

RS305P_BAUD = 9600
TIMEOUT = 0.5
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1
SLAVE_ADDR = 1
REG_U_DISPLAY = 0x0010  # lecture tension affichée (FC 03)


def _crc16_modbus(data: bytes) -> int:
    """CRC-16 Modbus (polynôme A001)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def _build_read_frame(addr: int, reg: int) -> bytes:
    """Trame Modbus FC 03 : lecture d'un registre."""
    payload = bytes([addr, 0x03, (reg >> 8) & 0xFF, reg & 0xFF, 0x00, 0x01])
    crc = _crc16_modbus(payload)
    return payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def _log(log_lines: List[str], msg: str) -> None:
    log_lines.append(msg)
    if msg.strip():
        logger.debug("détection: %s", msg)


def detect_rs305p(
    ports: List[str],
    log_lines: Optional[List[str]] = None,
    unusable_ports: Optional[Set[str]] = None,
) -> Optional[SerialDetectionResult]:
    """
    Cherche une alimentation RS305P sur la liste de ports (Modbus 9600, lecture registre).
    Les ports en erreur grave sont ajoutés à unusable_ports.
    """
    if log_lines is None:
        log_lines = []
    logger.debug("detect_rs305p: début — %d port(s) à tester: %s (baud=%s)", len(ports), ports, RS305P_BAUD)
    for i, port in enumerate(ports):
        logger.debug("detect_rs305p: test port %d/%d — %s", i + 1, len(ports), port)
        if _try_rs305p_on_port(port, log_lines, unusable_ports=unusable_ports):
            logger.info("Alimentation RS305P détectée sur %s", port)
            _log(log_lines, f"# Alimentation trouvée sur {port}.")
            logger.debug("detect_rs305p: trouvé sur %s", port)
            return SerialDetectionResult(port=port, baudrate=RS305P_BAUD)
        logger.debug("detect_rs305p: %s non RS305P, passage au port suivant", port)
    logger.debug("detect_rs305p: fin — aucune alimentation RS305P trouvée")
    return None


def _try_rs305p_on_port(
    port: str,
    log_lines: List[str],
    unusable_ports: Optional[Set[str]] = None,
) -> bool:
    """Ouvre le port en 9600, envoie lecture registre U_DISPLAY, vérifie réponse Modbus valide."""
    logger.debug("_try_rs305p_on_port: %s ouverture @ %s bauds (Modbus FC03 reg=0x%04X)", port, RS305P_BAUD, REG_U_DISPLAY)
    _log(log_lines, f"{port} [RS305P] Ouverture {RS305P_BAUD} bauds...")
    ser = None
    try:
        ser = serial.Serial(
            port=port,
            baudrate=RS305P_BAUD,
            bytesize=BYTESIZE,
            parity=PARITY,
            stopbits=STOPBITS,
            timeout=TIMEOUT,
            write_timeout=TIMEOUT,
        )
        frame = _build_read_frame(SLAVE_ADDR, REG_U_DISPLAY)
        _log(log_lines, f"{port} [RS305P] TX Modbus FC03")
        logger.debug("_try_rs305p_on_port: %s TX frame %s", port, frame.hex())
        ser.write(frame)
        resp = ser.read(7)
        ser.close()
        _log(log_lines, f"{port} [RS305P] Fermeture.")
        logger.debug("_try_rs305p_on_port: %s RX %d octets: %s", port, len(resp), resp.hex() if resp else "(vide)")
        if len(resp) < 5:
            logger.debug("_try_rs305p_on_port: %s réponse trop courte (%d < 5)", port, len(resp))
            return False
        if resp[0] != SLAVE_ADDR or resp[1] != 0x03:
            logger.debug("_try_rs305p_on_port: %s en-tête invalide (addr=%s, fc=%s)", port, resp[0], resp[1])
            return False
        if resp[1] & 0x80:
            logger.debug("_try_rs305p_on_port: %s exception Modbus (fc & 0x80)", port)
            return False  # exception Modbus
        # Vérifier CRC
        payload = resp[:5]
        crc_recv = resp[5] | (resp[6] << 8)
        crc_calc = _crc16_modbus(payload)
        if crc_calc != crc_recv:
            logger.debug("_try_rs305p_on_port: %s CRC invalide (reçu=0x%04X calculé=0x%04X)", port, crc_recv, crc_calc)
            return False
        _log(log_lines, f"{port} [RS305P] Accepté: oui")
        logger.debug("_try_rs305p_on_port: %s accepté (Modbus FC03 réponse valide)", port)
        return True
    except Exception as e:
        _log(log_lines, f"{port} [RS305P] Erreur: {e}")
        if unusable_ports is not None and _is_port_open_error(e):
            unusable_ports.add(port)
            logger.debug("_try_rs305p_on_port: %s erreur grave d'ouverture — port exclu des phases suivantes", port)
        else:
            logger.debug("_try_rs305p_on_port: %s exception — %s", port, e, exc_info=True)
        try:
            if ser is not None:
                ser.close()
        except Exception:
            pass
        return False
