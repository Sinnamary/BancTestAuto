"""
Backend USB (libusb) et liste de périphériques pour le DOS1102.
Séparé de dos1102_usb_connection pour réduire la complexité et permettre réutilisation.
"""
from typing import List, Tuple, Any, Optional

from .app_logger import get_logger

logger = get_logger(__name__)


def get_usb_backend() -> Optional[Any]:
    """
    Retourne un backend libusb utilisable par PyUSB (sous Windows le "default"
    ne charge souvent pas libusb, donc find() voit 0 périphérique).
    Essaie libusb1 puis libusb0. Retourne None si aucun backend disponible.
    """
    try:
        import usb.backend.libusb1
        backend = usb.backend.libusb1.get_backend()
        if backend is not None:
            logger.debug("Backend USB: libusb1 (libusb-1.0)")
            return backend
    except Exception as e:
        logger.debug("Backend libusb1 non disponible: %s", e)
    try:
        import usb.backend.libusb0
        backend = usb.backend.libusb0.get_backend()
        if backend is not None:
            logger.debug("Backend USB: libusb0")
            return backend
    except Exception as e:
        logger.debug("Backend libusb0 non disponible: %s", e)
    return None


def list_usb_devices() -> List[Tuple[int, int, str]]:
    """
    Liste les périphériques USB accessibles (PyUSB / libusb).
    Retourne une liste de (idVendor, idProduct, description).
    description peut être "VID:PID" ou "VID:PID — Product" si disponible.
    """
    logger.debug("list_usb_devices: démarrage")
    try:
        import usb.core
    except ImportError as e:
        logger.warning("PyUSB non installé : pip install pyusb — %s", e)
        return []

    backend = get_usb_backend()
    if backend is None:
        logger.warning(
            "Aucun backend libusb disponible. Sous Windows : installez libusb-1.0 "
            "(ex. libusb-1.0.dll dans le PATH ou via Zadig / libusb-win32). "
            "PyUSB ne peut pas voir les périphériques WinUSB sans ce backend."
        )
        return []
    logger.debug("list_usb_devices: utilisation backend %s", type(backend).__name__)

    result = []
    try:
        devs = usb.core.find(find_all=True, backend=backend)
        dev_list = list(devs)
        logger.debug("list_usb_devices: find(find_all=True) a retourné %d périphérique(s)", len(dev_list))
        for dev in dev_list:
            vid, pid = dev.idVendor, dev.idProduct
            desc = f"{vid:04x}:{pid:04x}"
            try:
                if dev.iProduct:
                    try:
                        import usb.util
                        s = usb.util.get_string(dev, dev.iProduct)
                        if s:
                            desc = f"{desc} — {s}"
                    except Exception as get_str_err:
                        logger.debug("list_usb_devices: get_string pour %04x:%04x: %s", vid, pid, get_str_err)
            except Exception:
                pass
            logger.debug("list_usb_devices: trouvé %04x:%04x — %s", vid, pid, desc)
            result.append((vid, pid, desc))
        logger.info("Rafraîchissement USB : %d périphérique(s) trouvé(s)", len(result))
    except Exception as e:
        logger.exception("list_usb_devices: erreur %s", e)
        logger.debug("list_usb_devices: traceback ci-dessus")
    return result


def is_usb_timeout_error(exc: Exception) -> bool:
    """True si l'exception correspond à un timeout de lecture USB (pas de données reçues)."""
    msg = str(exc)
    return "timeout error" in msg or "Operation timed out" in msg or "10060" in msg


def is_usb_device_error(exc: Exception) -> bool:
    """True si l'exception correspond à une erreur périphérique / pipe cassé."""
    msg = str(exc)
    return (
        "reaping request failed" in msg
        or "périphérique attaché au système ne fonctionne pas correctement" in msg
        or "device not functioning" in msg
    )
