"""
Détecteur alimentation RS305P (Modbus RTU, 9600 baud, lecture registre).
"""
from typing import List, Optional

import serial

from ..app_logger import get_logger
from .result import SerialDetectionResult

logger = get_logger(__name__)

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


def detect_rs305p(ports: List[str], log_lines: Optional[List[str]] = None) -> Optional[SerialDetectionResult]:
    """
    Cherche une alimentation RS305P sur la liste de ports (Modbus 9600, lecture registre).
    Retourne SerialDetectionResult si trouvé, None sinon.
    """
    if log_lines is None:
        log_lines = []
    for port in ports:
        if _try_rs305p_on_port(port, log_lines):
            logger.info("Alimentation RS305P détectée sur %s", port)
            _log(log_lines, f"# Alimentation trouvée sur {port}.")
            return SerialDetectionResult(port=port, baudrate=RS305P_BAUD)
    return None


def _try_rs305p_on_port(port: str, log_lines: List[str]) -> bool:
    """Ouvre le port en 9600, envoie lecture registre U_DISPLAY, vérifie réponse Modbus valide."""
    _log(log_lines, f"{port} [RS305P] Ouverture {RS305P_BAUD} bauds...")
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
        ser.write(frame)
        resp = ser.read(7)
        ser.close()
        _log(log_lines, f"{port} [RS305P] Fermeture.")
        if len(resp) < 5:
            return False
        if resp[0] != SLAVE_ADDR or resp[1] != 0x03:
            return False
        if resp[1] & 0x80:
            return False  # exception Modbus
        # Vérifier CRC
        payload = resp[:5]
        crc_recv = resp[5] | (resp[6] << 8)
        crc_calc = _crc16_modbus(payload)
        if crc_calc != crc_recv:
            return False
        _log(log_lines, f"{port} [RS305P] Accepté: oui")
        return True
    except Exception as e:
        _log(log_lines, f"{port} [RS305P] Erreur: {e}")
        try:
            ser.close()
        except Exception:
            pass
        return False
