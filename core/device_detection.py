"""
Détection automatique : parcours des ports COM, identification OWON (SCPI *IDN?)
et FY6900, retour des ports par équipement. Option mise à jour config.
Produit un log détaillé (port, débit, TX, RX) pour diagnostic dans l'interface.
"""
from typing import Optional

import serial
import serial.tools.list_ports

from .app_logger import get_logger

logger = get_logger(__name__)


def _log_detection(log_lines: list[str], msg: str) -> None:
    """Ajoute une ligne au log détaillé et la journalise en DEBUG (sauf ligne vide)."""
    log_lines.append(msg)
    if msg.strip():
        logger.debug("détection: %s", msg)

# Débit commun aux deux appareils (OWON et FY6900)
DETECTION_BAUD = 115200
OWON_BAUDS = [DETECTION_BAUD]
FY6900_BAUD = DETECTION_BAUD
TIMEOUT = 0.5
# Paramètres série utilisés pour tous les tests (pyserial défaut = 8N1)
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1


def _serial_params_str(baud: int) -> str:
    """Chaîne descriptive des paramètres série pour le log."""
    return f"{baud} bauds, {BYTESIZE} bits, parité {PARITY}, {STOPBITS} stop bit(s), timeout={TIMEOUT}s"


def list_serial_ports() -> list[str]:
    """Retourne la liste des ports série disponibles (COMx sous Windows, /dev/tty... sous Linux)."""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def _try_owon_on_port(port: str, log_lines: list[str]) -> tuple[bool, Optional[int]]:
    """Teste si un port répond en SCPI *IDN? et contient OWON ou XDM. Remplit log_lines.
    Retourne (succès, baud_utilisé) pour que la config puisse enregistrer le bon débit."""
    cmd = "*IDN?\\n"
    for baud in OWON_BAUDS:
        _log_detection(log_lines, f"{port} [OWON] Paramètres testés: {_serial_params_str(baud)}")
        _log_detection(log_lines, f"{port} {baud} [OWON] Ouverture...")
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
            _log_detection(log_lines, f"{port} {baud} [OWON] TX {cmd!r}")
            ser.write(b"*IDN?\n")
            raw = ser.readline()
            rx_str = raw.decode("utf-8", errors="replace").strip() if raw else ""
            if rx_str:
                _log_detection(log_lines, f"{port} {baud} [OWON] RX {rx_str!r}")
            else:
                _log_detection(log_lines, f"{port} {baud} [OWON] RX (timeout ou vide)")
            ser.close()
            _log_detection(log_lines, f"{port} {baud} [OWON] Fermeture.")
            if rx_str and ("OWON" in rx_str.upper() or "XDM" in rx_str.upper()):
                _log_detection(log_lines, f"{port} {baud} [OWON] Identifié: oui")
                return (True, baud)
            _log_detection(log_lines, f"{port} {baud} [OWON] Identifié: non")
        except Exception as e:
            _log_detection(log_lines, f"{port} {baud} [OWON] RX (erreur: {e})")
            _log_detection(log_lines, f"{port} {baud} [OWON] Fermeture.")
            try:
                ser.close()
            except Exception:
                pass
    return (False, None)


def _try_fy6900_on_port(port: str, log_lines: list[str]) -> bool:
    """
    Teste si un port répond au protocole FY6900 (commande WMW0 + LF).
    On n'accepte que si le port renvoie des données (réponse non vide), pour éviter
    de prendre une alimentation ou un autre appareil muet pour un FY6900.
    On rejette aussi toute réponse qui ressemble à du SCPI (ex. OWON).
    """
    cmd = "WMW0\\n"
    _log_detection(log_lines, f"{port} [FY6900] Paramètres testés: {_serial_params_str(FY6900_BAUD)}")
    _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] Ouverture...")
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
        _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] TX {cmd!r}")
        ser.write(b"WMW0\n")
        data = ser.read(10)
        if data:
            rx_str = data.decode("utf-8", errors="replace").strip() or data.hex(" ")
            _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] RX {rx_str!r}")
        else:
            _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] RX (timeout ou vide)")
        ser.close()
        # Ne pas accepter si pas de réponse : évite de prendre une alimentation (COM6) pour un FY6900
        if not data:
            _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] Fermeture. Accepté: non (aucune réponse)")
            return False
        # Rejeter si la réponse ressemble à du SCPI (autre appareil sur le même port)
        decoded = data.decode("utf-8", errors="replace")
        if "OWON" in decoded.upper() or "XDM" in decoded.upper() or "*IDN" in decoded.upper():
            _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] Fermeture. Accepté: non (réponse SCPI)")
            return False
        _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] Fermeture. Accepté: oui")
        return True
    except Exception as e:
        _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] RX (erreur: {e})")
        _log_detection(log_lines, f"{port} {FY6900_BAUD} [FY6900] Fermeture. Accepté: non")
        try:
            ser.close()
        except Exception:
            pass
        return False


def detect_devices() -> tuple[Optional[str], Optional[int], Optional[str], Optional[int], list[str]]:
    """
    Détection en deux phases :
    1) Chercher le multimètre OWON : on parcourt les ports jusqu'à en trouver un ; dès qu'il est
       identifié, on arrête et on ne reteste plus ce port ni les suivants pour l'OWON.
    2) Chercher le générateur FY6900 : on ne teste que les ports non utilisés par le multimètre.
    Un port identifié pour un instrument n'est plus jamais testé pour un autre.
    Retourne (port_multimetre, baud_multimetre, port_generateur, baud_generateur, log_detaille).
    Les bauds permettent de reconnecter avec le bon débit (évite pastille restant rouge).
    """
    ports = list_serial_ports()
    logger.info("Détection équipements — ports trouvés: %s", ports)
    log_lines: list[str] = []
    _log_detection(log_lines, "# Détection démarrée")
    _log_detection(log_lines, f"# Ports à scanner: {ports}")
    _log_detection(log_lines, f"# Paramètres série (tous les tests): {BYTESIZE} bits, parité {PARITY}, {STOPBITS} stop bit(s), timeout={TIMEOUT}s")

    # Phase 1 : chercher le multimètre OWON (on s'arrête dès qu'on le trouve)
    multimeter_port = None
    multimeter_baud: Optional[int] = None
    _log_detection(log_lines, "")
    _log_detection(log_lines, "# Phase 1 — Recherche du multimètre OWON (SCPI *IDN?)")
    for port in ports:
        ok, baud = _try_owon_on_port(port, log_lines)
        if ok:
            multimeter_port = port
            multimeter_baud = baud
            logger.info("Multimètre OWON détecté sur %s à %s bauds", port, baud)
            _log_detection(log_lines, f"# Multimètre trouvé sur {port} à {baud} bauds.")
            break

    # Phase 2 : chercher le générateur FY6900 uniquement sur les ports non utilisés par l'OWON
    generator_port = None
    generator_baud: Optional[int] = None
    ports_restants = [p for p in ports if p != multimeter_port]
    _log_detection(log_lines, "")
    _log_detection(log_lines, f"# Phase 2 — Recherche du générateur FY6900 (ports restants: {ports_restants})")
    for port in ports_restants:
        if _try_fy6900_on_port(port, log_lines):
            generator_port = port
            generator_baud = FY6900_BAUD
            logger.info("Générateur FY6900 détecté sur %s", port)
            _log_detection(log_lines, f"# Générateur trouvé sur {port}.")
            break

    _log_detection(log_lines, "")
    _log_detection(log_lines, f"# Détection terminée — multimètre={multimeter_port}@{multimeter_baud}, générateur={generator_port}@{generator_baud}")
    logger.info("Détection terminée — multimètre=%s@%s, générateur=%s@%s", multimeter_port, multimeter_baud, generator_port, generator_baud)
    return (multimeter_port, multimeter_baud, generator_port, generator_baud, log_lines)


def update_config_ports(
    config: dict,
    multimeter_port: Optional[str],
    generator_port: Optional[str],
    multimeter_baud: Optional[int] = None,
    generator_baud: Optional[int] = None,
) -> dict:
    """
    Retourne une copie de config avec serial_multimeter/generator.port et .baudrate
    mis à jour (port et baud utilisés lors de la détection pour que la reconnexion réussisse).
    Ne modifie pas le fichier.
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
    if multimeter_baud is not None:
        out["serial_multimeter"]["baudrate"] = multimeter_baud
    if generator_port is not None:
        out["serial_generator"]["port"] = generator_port
    if generator_baud is not None:
        out["serial_generator"]["baudrate"] = generator_baud

    return out
