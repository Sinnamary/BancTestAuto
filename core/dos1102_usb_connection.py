"""
Connexion USB (WinUSB / PyUSB) pour l'oscilloscope HANMATEK DOS1102.
Interface compatible avec SerialConnection : write(data), readline(), is_open(), close().
Utilise les transferts bulk USB pour envoyer/recevoir les commandes SCPI.
"""
from __future__ import annotations

import threading
from typing import List, Optional, Tuple

from .app_logger import get_logger
from .dos1102_usb_backend import (
    get_usb_backend,
    list_usb_devices,
    is_usb_timeout_error,
    is_usb_device_error,
)

logger = get_logger(__name__)

# Constantes pour transferts bulk (timeout ms)
# Certains échanges (mesures, forme d'onde complète) peuvent être un peu longs ;
# on utilise un timeout de lecture plus large pour laisser le temps à l'oscilloscope.
USB_READ_TIMEOUT = 5000
USB_WRITE_TIMEOUT = 2000
READ_CHUNK_SIZE = 256


class Dos1102UsbConnection:
    """
    Connexion USB type WinUSB/libusb pour le DOS1102.
    Même interface que SerialConnection : write(data: bytes), read(size), readline() -> bytes, is_open(), close().
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
            backend = get_usb_backend()
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

    def flush_input(self, timeout_ms: int = 50, max_reads: int = 50) -> int:
        """
        Vide le tampon d'entrée USB (données en attente d'une session précédente).
        Lit par blocs avec timeout court jusqu'à vide ou max_reads. Retourne le nombre d'octets jetés.
        """
        if self._dev is None or self._ep_in is None:
            return 0
        total = 0
        for _ in range(max_reads):
            try:
                data = self.read(1024, timeout_ms=timeout_ms)
                if not data:
                    break
                total += len(data)
                logger.debug("USB flush_input: jeté %d octets (total %d)", len(data), total)
            except Exception:
                break
        if total:
            logger.debug("USB flush_input: total %d octets jetés", total)
        return total

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

    def read(self, size: int = 1, timeout_ms: Optional[int] = None) -> bytes:
        """Lit jusqu'à size octets (pour format bloc SCPI ex. forme d'onde). timeout_ms optionnel pour cette lecture."""
        with self._lock:
            if self._dev is None or self._ep_in is None:
                raise OSError("Connexion USB non ouverte")
            if size <= 0:
                return b""
            timeout = timeout_ms if timeout_ms is not None else self._read_timeout
            logger.debug(
                "USB read: entrée size=%d, timeout=%d ms, endpoint IN=0x%02x",
                size, timeout, self._ep_in.bEndpointAddress,
            )
            buf = []
            need = size
            while need > 0:
                chunk_size = min(need, READ_CHUNK_SIZE)
                try:
                    chunk = self._ep_in.read(chunk_size, timeout=timeout)
                except Exception as e:
                    if is_usb_timeout_error(e):
                        logger.debug(
                            "USB read: timeout (%d ms) sans données (demande=%d octets, chunk=%d)",
                            timeout, size, chunk_size,
                        )
                        break
                    if is_usb_device_error(e):
                        logger.error(
                            "USB read: erreur périphérique (%s), arrêt de la lecture (demande=%d octets)",
                            str(e), size,
                        )
                        break
                    logger.exception("USB read(%d) erreur (non-timeout): %s", size, e)
                    raise
                chunk = bytes(chunk)
                if not chunk:
                    logger.debug("USB read: chunk vide, sortie")
                    break
                logger.debug(
                    "USB read: reçu chunk %d octets: %r",
                    len(chunk),
                    chunk[:120] if len(chunk) > 120 else chunk,
                )
                buf.append(chunk)
                need -= len(chunk)
            result = b"".join(buf)
            logger.debug("USB read: retour total %d octets", len(result))
            return result

    def readline(self) -> bytes:
        """Lit jusqu'à un LF (0x0a). Lit par paquets pour constituer une ligne."""
        with self._lock:
            if self._dev is None or self._ep_in is None:
                raise OSError("Connexion USB non ouverte")
            logger.debug(
                "USB readline: attente réponse (timeout=%d ms, endpoint IN 0x%02x)",
                self._read_timeout,
                self._ep_in.bEndpointAddress,
            )
            buf = []
            try:
                while True:
                    try:
                        chunk = self._ep_in.read(READ_CHUNK_SIZE, timeout=self._read_timeout)
                    except Exception as e:
                        if is_usb_timeout_error(e):
                            logger.warning(
                                "USB readline: timeout (%d ms) sans données (endpoint 0x%02x)",
                                self._read_timeout, self._ep_in.bEndpointAddress,
                            )
                            break
                        if is_usb_device_error(e):
                            logger.error(
                                "USB readline: erreur périphérique (%s), arrêt de la lecture (endpoint 0x%02x)",
                                str(e), self._ep_in.bEndpointAddress,
                            )
                            break
                        logger.exception("USB readline erreur (non-timeout): %s", e)
                        raise
                    if not chunk:
                        logger.debug("USB readline: chunk vide, fin")
                        break
                    chunk = bytes(chunk)
                    buf.append(chunk)
                    logger.debug(
                        "USB readline: reçu %d octets: %r",
                        len(chunk),
                        chunk[:80] if len(chunk) > 80 else chunk,
                    )
                    if b"\n" in chunk:
                        break
            except Exception:
                # Les erreurs non liées au timeout sont déjà loguées ci‑dessus.
                raise
            line = b"".join(buf)
            logger.debug("USB readline: total %d octets", len(line))
            if line:
                logger.debug("USB RX: %r", line.decode("utf-8", errors="replace").strip() or line.hex(" "))
            elif buf:
                logger.debug("USB readline: aucun LF reçu, buffer total %d octets", sum(len(b) for b in buf))
            return line
