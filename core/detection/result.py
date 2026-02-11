"""
Types de résultat de détection (série, USB, agrégat).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from ..equipment import EquipmentKind


@dataclass
class SerialDetectionResult:
    """Résultat de détection pour un équipement série (port COM)."""
    port: Optional[str] = None
    baudrate: Optional[int] = None

    @property
    def detected(self) -> bool:
        return self.port is not None


@dataclass
class UsbDetectionResult:
    """Résultat de détection pour un équipement USB (VID:PID)."""
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None

    @property
    def detected(self) -> bool:
        return self.vendor_id is not None and self.product_id is not None


DetectionResultItem = Union[SerialDetectionResult, UsbDetectionResult]


@dataclass
class BenchDetectionResult:
    """Résultat global de la détection (un résultat par type d'équipement + log)."""
    results: Dict[EquipmentKind, DetectionResultItem] = field(default_factory=dict)
    log_lines: List[str] = field(default_factory=list)

    def get_serial(self, kind: EquipmentKind) -> Optional[SerialDetectionResult]:
        """Retourne le résultat série pour un kind, ou None."""
        r = self.results.get(kind)
        if isinstance(r, SerialDetectionResult):
            return r
        return None

    def get_usb(self, kind: EquipmentKind) -> Optional[UsbDetectionResult]:
        """Retourne le résultat USB pour un kind, ou None."""
        r = self.results.get(kind)
        if isinstance(r, UsbDetectionResult):
            return r
        return None
