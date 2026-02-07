"""
Fichier de log des émissions/réceptions série : un fichier par lancement, horodaté.
Créé au premier écrit ; chaque ligne : [timestamp] [origine] [TX|RX] données.
"""
from datetime import datetime
from pathlib import Path
import threading


class SerialExchangeLogger:
    """
    Un fichier de log par session (lancement), nommé serial_YYYY-MM-DD_HH-MM-SS.log.
    Thread-safe (un lock pour les écritures).
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
        self._file.flush()

    def log(self, origin: str, direction: str, data: str) -> None:
        """Enregistre une ligne : origin = 'multimeter'|'generator', direction = 'TX'|'RX'."""
        with self._lock:
            self._ensure_file()
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            line = f"[{ts}] [{origin}] [{direction}] {data!r}\n"
            self._file.write(line)
            self._file.flush()

    def get_callback(self, origin: str):
        """Retourne un callback (direction, message) pour SerialConnection."""
        def callback(direction: str, message: str) -> None:
            self.log(origin, direction, message)
        return callback

    def close(self) -> None:
        with self._lock:
            if self._file:
                try:
                    self._file.close()
                except Exception:
                    pass
                self._file = None
