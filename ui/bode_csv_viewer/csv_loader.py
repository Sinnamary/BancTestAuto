"""
Chargement CSV Banc filtre. Types et logique propres au viewer, sans lien avec core.
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional

from .model import BodeCsvPoint, BodeCsvDataset


class BodeCsvColumnMap:
    """Mapping des colonnes CSV par en-tête (insensible à la casse)."""
    def __init__(self, header: List[str]):
        self._indices: Dict[str, int] = {}
        for i, col in enumerate(header):
            key = col.strip().lower().replace(" ", "").replace("_", "")
            if "fhz" in key or "f_hz" in key or key == "f":
                self._indices["f_hz"] = i
            elif "usv" in key or "us_v" in key:
                self._indices["us_v"] = i
            elif "uev" in key or "ue_v" in key:
                self._indices["ue_v"] = i
            elif "usue" in key or "us/ue" in key or "gainlinear" in key:
                self._indices["gain_linear"] = i
            elif "gaindb" in key or ("gain" in key and "db" in key):
                self._indices["gain_db"] = i
            elif "phasedeg" in key or "phase_deg" in key or "phase" in key:
                self._indices["phase_deg"] = i
        if "f_hz" not in self._indices:
            self._indices["f_hz"] = 0
        if "gain_db" not in self._indices:
            self._indices["gain_db"] = 3
        if "us_v" not in self._indices:
            self._indices["us_v"] = 1
        if "gain_linear" not in self._indices:
            self._indices["gain_linear"] = 2

    def get(self, name: str, default: Optional[int] = None) -> Optional[int]:
        return self._indices.get(name, default)

    def has(self, name: str) -> bool:
        return name in self._indices


class BodeCsvFileLoader:
    """Charge un fichier CSV Banc filtre et retourne un BodeCsvDataset."""
    DEFAULT_SEP = ";"
    ENCODING = "utf-8"

    def load(self, path: str) -> BodeCsvDataset:
        points: List[BodeCsvPoint] = []
        with open(path, "r", newline="", encoding=self.ENCODING) as f:
            reader = csv.reader(f, delimiter=self.DEFAULT_SEP)
            header = next(reader, None)
            if not header:
                return BodeCsvDataset(points)
            col_map = BodeCsvColumnMap(header)
            for row in reader:
                if len(row) < 4:
                    continue
                pt = self._row_to_point(row, col_map)
                if pt is not None:
                    points.append(pt)
        return BodeCsvDataset(points)

    def _row_to_point(self, row: List[str], col_map: BodeCsvColumnMap) -> Optional[BodeCsvPoint]:
        try:
            i_f = col_map.get("f_hz", 0)
            i_us = col_map.get("us_v", 1)
            i_lin = col_map.get("gain_linear", 2)
            i_db = col_map.get("gain_db", 3)
            if i_f is None or i_db is None:
                return None
            f_hz = float(row[i_f].replace(",", "."))
            us_v = float(row[i_us].replace(",", ".")) if i_us is not None and i_us < len(row) else 0.0
            g_db = float(row[i_db].replace(",", "."))
            g_lin = float(row[i_lin].replace(",", ".")) if i_lin is not None and i_lin < len(row) else self._db_to_linear(g_db)
            ue_v: Optional[float] = None
            if col_map.has("ue_v"):
                idx = col_map.get("ue_v")
                if idx is not None and idx < len(row) and row[idx].strip():
                    try:
                        ue_v = float(row[idx].replace(",", "."))
                    except ValueError:
                        pass
            phase_deg: Optional[float] = None
            if col_map.has("phase_deg"):
                idx = col_map.get("phase_deg")
                if idx is not None and idx < len(row) and row[idx].strip():
                    try:
                        phase_deg = float(row[idx].replace(",", "."))
                    except ValueError:
                        pass
            return BodeCsvPoint(f_hz=f_hz, us_v=us_v, gain_linear=g_lin, gain_db=g_db, ue_v=ue_v, phase_deg=phase_deg)
        except (ValueError, IndexError, KeyError):
            return None

    @staticmethod
    def _db_to_linear(g_db: float) -> float:
        if g_db <= -200:
            return 0.0
        return 10 ** (g_db / 20.0)
