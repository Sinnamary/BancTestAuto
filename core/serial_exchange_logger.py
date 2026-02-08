"""
Fichier de log des émissions/réceptions série : un fichier par lancement, horodaté.
Créé au premier écrit ; chaque ligne : [timestamp] [origine] port baudrate [TX|RX] données.
"""
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional


class SerialExchangeLogger:
    """
    Un fichier de log par session (lancement), nommé serial_YYYY-MM-DD_HH-MM-SS.log.
    Thread-safe (un lock pour les écritures).
    Chaque ligne inclut port et baudrate si fournis pour faciliter le diagnostic.
    """

    def __init__(self, log_dir: str = "logs"):
        self._log_dir = Path(log_dir)
        self._file = None
        self._path = None
        self._lock = threading.Lock()

    def _ensure_file(self) -> None:
        if self._file is not None:
            return
        self._log_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        self._path = self._log_dir / f"serial_{now:%Y-%m-%d_%H-%M-%S}.log"
        self._file = open(self._path, "a", encoding="utf-8")
        self._file.write(f"# Session started {now.isoformat()}\n")
        self._file.write("# Format: [HH:MM:SS.ms] [origin] port baudrate [TX|RX] data\n")
        self._file.flush()

    def log(
        self,
        origin: str,
        direction: str,
        data: str,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
    ) -> None:
        """Enregistre une ligne : origin = 'multimeter'|'generator', direction = 'TX'|'RX'.
        port et baudrate optionnels pour identifier la liaison."""
        with self._lock:
            self._ensure_file()
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            port_str = str(port) if port else "-"
            baud_str = str(baudrate) if baudrate is not None else "-"
            line = f"[{ts}] [{origin}] {port_str} {baud_str} [{direction}] {data!r}\n"
            self._file.write(line)
            self._file.flush()

    def get_callback(
        self,
        origin: str,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
    ):
        """Retourne un callback (direction, message) pour SerialConnection.
        port et baudrate sont enregistrés à chaque ligne pour le diagnostic."""
        def callback(direction: str, message: str) -> None:
            self.log(origin, direction, message, port=port, baudrate=baudrate)
        return callback

    def close(self) -> None:
        with self._lock:
            if self._file:
                try:
                    self._file.close()
                except Exception:
                    pass
                self._file = None
