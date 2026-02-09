"""
Connexion USB (WinUSB / PyUSB) pour l'oscilloscope HANMATEK DOS1102.
Interface compatible avec SerialConnection : write(data), readline(), is_open(), close().
Utilise les transferts bulk USB pour envoyer/recevoir les commandes SCPI.
"""
from __future__ import annotations

import threading
from typing import List, Optional, Tuple

from .app_logger import get_logger

logger = get_logger(__name__)

# Constantes pour transferts bulk (timeout ms)
USB_READ_TIMEOUT = 2000
USB_WRITE_TIMEOUT = 2000
READ_CHUNK_SIZE = 256


def _get_usb_backend():
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

    backend = _get_usb_backend()
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


class Dos1102UsbConnection:
    """
    Connexion USB type WinUSB/libusb pour le DOS1102.
    Même interface que SerialConnection : write(data: bytes), readline() -> bytes, is_open(), close().
    """

    def __init__(
        self,
        id_vendor: int,
        id_product: int,
        read_timeout_ms: int = USB_READ_TIMEOUT,
        write_timeout_ms: int = USB_WRITE_TIMEOUT,
    ):
        self._id_vendor = id_vendor
        self._id_product = id_product
        self._read_timeout = read_timeout_ms
        self._write_timeout = write_timeout_ms
        self._dev = None
        self._ep_out = None
        self._ep_in = None
        self._lock = threading.Lock()

    def is_open(self) -> bool:
        return self._dev is not None

    def open(self) -> None:
        import usb.core
        import usb.util

        logger.debug("Dos1102UsbConnection.open: recherche %04x:%04x", self._id_vendor, self._id_product)
        with self._lock:
            if self._dev is not None:
                return
            backend = _get_usb_backend()
            if backend is None:
                raise OSError(
                    "Backend libusb introuvable. Installez libusb-1.0 (sous Windows : libusb-1.0.dll, ou via Zadig)."
                )
            dev = usb.core.find(idVendor=self._id_vendor, idProduct=self._id_product, backend=backend)
            logger.debug("Dos1102UsbConnection.open: find() -> %s", dev)
            if dev is None:
                raise OSError(
                    f"Périphérique USB {self._id_vendor:04x}:{self._id_product:04x} introuvable. "
                    "Vérifiez le câble et que le pilote WinUSB est installé (Zadig)."
                )
            try:
                if dev.is_kernel_driver_active(0):
                    dev.detach_kernel_driver(0)
                    logger.debug("Dos1102UsbConnection.open: kernel driver détaché")
            except Exception as detach_err:
                logger.debug("Dos1102UsbConnection.open: detach_kernel_driver: %s", detach_err)
            logger.debug("Dos1102UsbConnection.open: set_configuration()")
            dev.set_configuration()
            cfg = dev.get_active_configuration()
            intf = cfg[(0, 0)]
            ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT,
            )
            ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN,
            )
            if ep_out is None or ep_in is None:
                usb.util.dispose_resources(dev)
                raise OSError("Endpoints bulk OUT/IN introuvables sur ce périphérique.")
            self._dev = dev
            self._ep_out = ep_out
            self._ep_in = ep_in
            logger.debug(
                "USB OPEN %04x:%04x — OUT=0x%02x IN=0x%02x",
                self._id_vendor, self._id_product,
                ep_out.bEndpointAddress, ep_in.bEndpointAddress,
            )

    def close(self) -> None:
        with self._lock:
            if self._dev is None:
                return
            try:
                import usb.util
                usb.util.dispose_resources(self._dev)
            except Exception:
                pass
            logger.debug("USB CLOSE %04x:%04x", self._id_vendor, self._id_product)
            self._dev = None
            self._ep_out = None
            self._ep_in = None

    def write(self, data: bytes) -> int:
        with self._lock:
            if self._dev is None or self._ep_out is None:
                raise OSError("Connexion USB non ouverte")
            logger.debug("USB write: envoi %d octets, endpoint OUT 0x%02x", len(data), self._ep_out.bEndpointAddress)
            try:
                n = self._ep_out.write(data, timeout=self._write_timeout)
                logger.debug("USB write: %d octets envoyés, contenu: %r", n, data.decode("utf-8", errors="replace").strip() or data.hex())
                return n
            except Exception as e:
                logger.exception("USB write erreur: %s", e)
                raise

    def readline(self) -> bytes:
        """Lit jusqu'à un LF (0x0a). Lit par paquets pour constituer une ligne."""
        with self._lock:
            if self._dev is None or self._ep_in is None:
                raise OSError("Connexion USB non ouverte")
            logger.debug("USB readline: attente réponse (timeout=%d ms, endpoint IN 0x%02x)", self._read_timeout, self._ep_in.bEndpointAddress)
            buf = []
            try:
                while True:
                    chunk = self._ep_in.read(READ_CHUNK_SIZE, timeout=self._read_timeout)
                    if not chunk:
                        logger.debug("USB readline: chunk vide, fin")
                        break
                    chunk = bytes(chunk)
                    buf.append(chunk)
                    logger.debug("USB readline: reçu %d octets: %r", len(chunk), chunk[:80] if len(chunk) > 80 else chunk)
                    if b"\n" in chunk:
                        break
            except Exception as e:
                logger.exception("USB readline erreur (timeout?): %s", e)
                raise
            line = b"".join(buf)
            logger.debug("USB readline: total %d octets", len(line))
            if line:
                logger.debug("USB RX: %r", line.decode("utf-8", errors="replace").strip() or line.hex(" "))
            elif buf:
                logger.debug("USB readline: aucun LF reçu, buffer total %d octets", sum(len(b) for b in buf))
            return line
