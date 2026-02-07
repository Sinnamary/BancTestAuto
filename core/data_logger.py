"""
Enregistrement CSV horodaté : timestamp_iso, elapsed_s, value, unit, mode.
Utilisé par logging_view ; une mesure par intervalle.
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading
import time


class DataLogger:
    """
    Enregistre des mesures à intervalle régulier dans un fichier CSV.
    Format : timestamp_iso, elapsed_s, value, unit, mode.
    """

    def __init__(self):
        self._file = None
        self._writer = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._interval_s = 5.0
        self._output_dir = "./logs"
        self._measurement = None
        self._mode_str = "VOLT:DC"
        self._start_time: Optional[float] = None
        self._on_point = None  # callback(timestamp_iso, elapsed_s, value, unit, mode)

    def set_measurement(self, measurement):
        self._measurement = measurement

    def set_on_point_callback(self, callback):
        """callback(timestamp_iso, elapsed_s, value, unit, mode) pour mise à jour UI."""
        self._on_point = callback

    def start(
        self,
        output_dir: str = None,
        interval_s: float = None,
        mode_str: str = None,
    ) -> Optional[str]:
        """
        Démarre l'enregistrement. Crée le fichier owon_log_YYYY-MM-DD_HH-MM-SS.csv.
        Retourne le chemin du fichier ou None en cas d'erreur.
        """
        if self._running or not self._measurement:
            return None
        if output_dir is not None:
            self._output_dir = output_dir
        if interval_s is not None:
            self._interval_s = max(0.5, float(interval_s))
        if mode_str is not None:
            self._mode_str = mode_str

        Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        filename = f"owon_log_{now:%Y-%m-%d_%H-%M-%S}.csv"
        filepath = Path(self._output_dir) / filename

        try:
            self._file = open(filepath, "w", newline="", encoding="utf-8")
            self._writer = csv.writer(self._file)
            self._writer.writerow(["timestamp_iso", "elapsed_s", "value", "unit", "mode"])
            self._file.flush()
        except Exception:
            return None

        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return str(filepath)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._interval_s * 2)
            self._thread = None
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None
        self._writer = None

    def is_running(self) -> bool:
        return self._running

    def _run_loop(self) -> None:
        while self._running:
            t0 = time.time()
            try:
                raw = self._measurement.read_value()
                val = self._measurement.parse_float(raw)
                value_str = raw.strip() if val is None else f"{val}"
                elapsed = time.time() - self._start_time
                ts_iso = datetime.now().isoformat(timespec="milliseconds")
                unit = "V"
                if getattr(self._measurement, "get_unit_for_current_mode", None):
                    unit = self._measurement.get_unit_for_current_mode()
                row = [ts_iso, f"{elapsed:.2f}", value_str, unit, self._mode_str]
                if self._writer:
                    self._writer.writerow(row)
                    if self._file:
                        self._file.flush()
                if self._on_point:
                    self._on_point(ts_iso, elapsed, value_str, unit, self._mode_str)
            except Exception:
                pass
            elapsed_loop = time.time() - t0
            sleep_time = max(0, self._interval_s - elapsed_loop)
            for _ in range(int(sleep_time * 10)):
                if not self._running:
                    break
                time.sleep(0.1)
