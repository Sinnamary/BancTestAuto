"""
Détection automatique : parcours des ports COM, identification OWON (SCPI *IDN?)
et FY6900, retour des ports par équipement. Option mise à jour config.
"""
from typing import Optional

import serial
import serial.tools.list_ports

from core.app_logger import get_logger

logger = get_logger(__name__)

# Débits à essayer pour chaque type
OWON_BAUDS = [9600, 115200]
FY6900_BAUD = 115200
TIMEOUT = 0.5


def list_serial_ports() -> list[str]:
    """Retourne la liste des ports série disponibles (COMx sous Windows, /dev/tty... sous Linux)."""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def _try_owon_on_port(port: str) -> bool:
    """Teste si un port répond en SCPI *IDN? et contient OWON ou XDM."""
    for baud in OWON_BAUDS:
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=TIMEOUT, write_timeout=TIMEOUT)
            ser.write(b"*IDN?\n")
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            ser.close()
            if line and ("OWON" in line.upper() or "XDM" in line.upper()):
                return True
        except Exception:
            try:
                ser.close()
            except Exception:
                pass
    return False


def _try_fy6900_on_port(port: str) -> bool:
    """Teste si un port répond au protocole FY6900 (commande WMW0 + LF)."""
    try:
        ser = serial.Serial(port=port, baudrate=FY6900_BAUD, timeout=TIMEOUT, write_timeout=TIMEOUT)
        ser.write(b"WMW0\n")
        # FY6900 renvoie souvent 0x0a après exécution
        data = ser.read(10)
        ser.close()
        # Accepte si pas d'exception (certains FY6900 ne répondent pas mais acceptent la commande)
        return True
    except Exception:
        try:
            ser.close()
        except Exception:
            pass
        return False


def detect_devices() -> tuple[Optional[str], Optional[str]]:
    """
    Parcourt les ports COM disponibles.
    Retourne (port_multimetre, port_generateur).
    Une valeur est None si aucun équipement trouvé.
    """
    ports = list_serial_ports()
    logger.info("Détection équipements — ports trouvés: %s", ports)
    multimeter_port = None
    generator_port = None

    for port in ports:
        if _try_owon_on_port(port):
            multimeter_port = port
            logger.info("Multimètre OWON détecté sur %s", port)
            if generator_port is not None:
                break
        if _try_fy6900_on_port(port):
            generator_port = port
            logger.info("Générateur FY6900 détecté sur %s", port)
            if multimeter_port is not None:
                break

    logger.info("Détection terminée — multimètre=%s, générateur=%s", multimeter_port, generator_port)
    return (multimeter_port, generator_port)


def update_config_ports(
    config: dict,
    multimeter_port: Optional[str],
    generator_port: Optional[str],
) -> dict:
    """
    Retourne une copie de config avec serial_multimeter.port et serial_generator.port
    mis à jour. Ne modifie pas le fichier.
    """
    out = dict(config)
    if "serial_multimeter" not in out:
        out["serial_multimeter"] = {}
    else:
        out["serial_multimeter"] = dict(out["serial_multimeter"])
    if "serial_generator" not in out:
        out["serial_generator"] = {}
    else:
        out["serial_generator"] = dict(out["serial_generator"])

    if multimeter_port is not None:
        out["serial_multimeter"]["port"] = multimeter_port
    if generator_port is not None:
        out["serial_generator"]["port"] = generator_port

    return out
