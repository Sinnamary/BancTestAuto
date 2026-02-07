"""
Liaison série : un port, buffers, option de log des échanges.
Pas de protocole (SCPI/FY6900) ; utilisé par ScpiProtocol et Fy6900Protocol.
"""
import threading
from typing import Callable, Optional

import serial
from serial import SerialException


class SerialConnection:
    """
    Une liaison série par instance (un port).
    Paramètres : port, baudrate, timeout, write_timeout, log_exchanges.
    """

    def __init__(
        self,
        port: str = "COM3",
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 2.0,
        write_timeout: float = 2.0,
        log_exchanges: bool = False,
        log_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self._port = port
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._timeout = timeout
        self._write_timeout = write_timeout
        self._log_exchanges = log_exchanges
        self._log_callback = log_callback or (lambda _dir, _msg: None)
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()

    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def open(self) -> None:
        """Ouvre le port série. Lève SerialException en cas d'erreur."""
        with self._lock:
            if self._serial and self._serial.is_open:
                return
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=self._bytesize,
                parity=self._parity,
                stopbits=self._stopbits,
                timeout=self._timeout,
                write_timeout=self._write_timeout,
            )

    def close(self) -> None:
        with self._lock:
            if self._serial:
                try:
                    self._serial.close()
                except Exception:
                    pass
                self._serial = None

    def write(self, data: bytes) -> int:
        """Écrit des octets. Lève SerialException si non connecté ou erreur."""
        with self._lock:
            if not self._serial or not self._serial.is_open:
                raise SerialException("Port non ouvert")
            n = self._serial.write(data)
            if self._log_exchanges:
                self._log_callback("TX", data.decode("utf-8", errors="replace"))
            return n

    def readline(self) -> bytes:
        """Lit jusqu'à un LF (0x0a). Timeout selon self._timeout."""
        with self._lock:
            if not self._serial or not self._serial.is_open:
                raise SerialException("Port non ouvert")
            line = self._serial.readline()
            if self._log_exchanges and line:
                self._log_callback("RX", line.decode("utf-8", errors="replace"))
            return line

    def read_until(self, terminator: bytes = b"\n") -> bytes:
        with self._lock:
            if not self._serial or not self._serial.is_open:
                raise SerialException("Port non ouvert")
            data = self._serial.read_until(terminator)
            if self._log_exchanges and data:
                self._log_callback("RX", data.decode("utf-8", errors="replace"))
            return data

    def set_log_exchanges(self, enabled: bool) -> None:
        self._log_exchanges = enabled

    def update_params(
        self,
        port: str | None = None,
        baudrate: int | None = None,
        timeout: float | None = None,
        write_timeout: float | None = None,
    ) -> None:
        """Met à jour les paramètres (prise en compte après close + open)."""
        if port is not None:
            self._port = port
        if baudrate is not None:
            self._baudrate = baudrate
        if timeout is not None:
            self._timeout = timeout
        if write_timeout is not None:
            self._write_timeout = write_timeout
