"""
Protocole Modbus RTU pour alimentation Rockseed RS305P.
Codes fonction : 03 (lecture), 06 (écriture).
Voir docs/Modbus.pdf.
"""
from .serial_connection import SerialConnection
from .app_logger import get_logger

logger = get_logger(__name__)

# Registres Modbus (adresses hex)
REG_ON_OFF = 0x0001  # 0=OFF, 1=ON
REG_U_DISPLAY = 0x0010  # tension affichée (2 décimales)
REG_I_DISPLAY = 0x0011  # courant affiché (3 décimales)
REG_SET_U = 0x0030  # tension cible (2 décimales)
REG_SET_I = 0x0031  # courant cible (3 décimales)


def _crc16_modbus(data: bytes) -> int:
    """Calcule le CRC-16 Modbus (polynôme A001)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def _build_frame(addr: int, func: int, data: bytes) -> bytes:
    """Construit une trame Modbus RTU : addr, func, data, CRC (low, high)."""
    payload = bytes([addr, func]) + data
    crc = _crc16_modbus(payload)
    return payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def _parse_response(frame: bytes, addr: int, func: int) -> bytes:
    """Vérifie addr/func et retourne la zone données. Lève ValueError si erreur."""
    if len(frame) < 5:
        raise ValueError("Réponse trop courte")
    if frame[0] != addr:
        raise ValueError(f"Adresse invalide: attendu {addr}, reçu {frame[0]}")
    if frame[1] & 0x80:
        raise ValueError(f"Exception Modbus: code {frame[2]}")
    if frame[1] != func:
        raise ValueError(f"Code fonction invalide: attendu {func}, reçu {frame[1]}")
    return frame[2:-2]


class Rs305pProtocol:
    """
    Pilote Modbus pour alimentation RS305P.
    Paramètres série : 9600 baud, 8N1.
    """

    def __init__(self, connection: SerialConnection, slave_addr: int = 1):
        self._conn = connection
        self._addr = slave_addr

    def _request_response(self, frame: bytes, response_len: int) -> bytes:
        """Envoie une trame et lit la réponse (response_len octets attendus)."""
        import time
        logger.debug("RS305P Modbus TX: %s", frame.hex(" "))
        self._conn.write(frame)
        time.sleep(0.02)
        resp = self._conn.read(response_len)
        logger.debug("RS305P Modbus RX: %s", resp.hex(" ") if resp else "(vide)")
        return resp

    def read_register(self, reg: int) -> int:
        """Lit un registre (FC 03). Retourne la valeur 16 bits."""
        data = bytes([
            (reg >> 8) & 0xFF,
            reg & 0xFF,
            0x00, 0x01,
        ])
        frame = _build_frame(self._addr, 0x03, data)
        resp = self._request_response(frame, 7)
        parsed = _parse_response(resp, self._addr, 0x03)
        if len(parsed) < 3 or parsed[0] != 2:
            raise ValueError("Format réponse lecture invalide")
        return (parsed[1] << 8) | parsed[2]

    def write_register(self, reg: int, value: int) -> None:
        """Écrit un registre (FC 06). value sur 16 bits."""
        data = bytes([
            (reg >> 8) & 0xFF,
            reg & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ])
        frame = _build_frame(self._addr, 0x06, data)
        resp = self._request_response(frame, 8)
        _parse_response(resp, self._addr, 0x06)

    def set_output(self, on: bool) -> None:
        """Sortie ON (True) ou OFF (False)."""
        self.write_register(REG_ON_OFF, 1 if on else 0)

    def get_output(self) -> bool:
        """Lit l'état de la sortie (ON/OFF)."""
        val = self.read_register(REG_ON_OFF)
        return val != 0

    def set_voltage(self, voltage_v: float) -> None:
        """Règle la tension cible (V). 2 décimales → valeur = voltage * 100."""
        raw = int(round(voltage_v * 100))
        raw = max(0, min(65535, raw))
        self.write_register(REG_SET_U, raw)

    def set_current(self, current_a: float) -> None:
        """Règle le courant cible (A). 3 décimales → valeur = current * 1000."""
        raw = int(round(current_a * 1000))
        raw = max(0, min(65535, raw))
        self.write_register(REG_SET_I, raw)

    def get_voltage(self) -> float:
        """Lit la tension affichée (V)."""
        raw = self.read_register(REG_U_DISPLAY)
        return raw / 100.0

    def get_current(self) -> float:
        """Lit le courant affiché (A)."""
        raw = self.read_register(REG_I_DISPLAY)
        return raw / 1000.0
