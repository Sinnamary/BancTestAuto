"""
Fichier de log des émissions/réceptions série : uniquement l’onglet Terminal série.
Un fichier par session, horodaté. Créé au premier écrit (choix d’un équipement ou premier TX/RX).
Format : une ligne "# Équipement: Nom (port ou USB)" au début du choix d’équipement, puis [timestamp] [TX|RX] données.
"""
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional


class SerialExchangeLogger:
    """
    Un fichier de log par session, nommé serial_YYYY-MM-DD_HH-MM-SS.log.
    Réservé au trafic de l’onglet Terminal série (TX/RX envoyés/reçus par l’utilisateur).
    Thread-safe. L’équipement connecté est indiqué une fois au début du choix.
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
        self._file.write("# Log Terminal série uniquement. Format: # Équipement: Nom (port/USB) puis [HH:MM:SS.ms] [TX|RX] data\n")
        self._file.flush()

    def log_equipment(self, equipment_label: str) -> None:
        """Écrit une ligne indiquant l’équipement connecté (une fois au début du choix dans le terminal)."""
        with self._lock:
            self._ensure_file()
            self._file.write(f"# Équipement: {equipment_label}\n")
            self._file.flush()

    def log(
        self,
        origin: str,
        direction: str,
        data: str,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
    ) -> None:
        """Enregistre une ligne TX ou RX du terminal série. origin = libellé équipement, direction = 'TX'|'RX'."""
        with self._lock:
            self._ensure_file()
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            line = f"[{ts}] [{direction}] {data!r}\n"
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
