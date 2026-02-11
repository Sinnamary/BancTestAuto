"""
État de connexion des équipements (modèle pur, sans UI).
Utilisé par le contrôleur de connexion et par l'UI pour afficher les pastilles.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

from .equipment import EquipmentKind, bench_equipment_kinds


@dataclass
class EquipmentState:
    """État d'un équipement : connecté ou non, port/device, modèle affiché."""
    kind: EquipmentKind
    connected: bool = False
    port_or_device: Optional[str] = None  # "COM3" ou "5345:1234" pour USB
    model_or_label: Optional[str] = None  # "XDM", "FY6900", etc.
    detected: bool = False  # True si détecté mais pas encore connecté

    def display_text(self) -> str:
        """Texte pour l'affichage (ex. 'Multimètre: XDM — COM3' ou 'Multimètre: Non connecté')."""
        from .equipment import equipment_display_name
        name = equipment_display_name(self.kind)
        if self.connected and (self.model_or_label or self.port_or_device):
            parts = [self.model_or_label or "", self.port_or_device or ""]
            return f"{name}: {' — '.join(p for p in parts if p)}"
        return f"{name}: Non connecté"


@dataclass
class BenchConnectionState:
    """État de connexion de l'ensemble du banc (un état par type d'équipement)."""
    _states: Dict[EquipmentKind, EquipmentState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._states:
            for kind in bench_equipment_kinds():
                self._states[kind] = EquipmentState(kind=kind)

    def get_state(self, kind: EquipmentKind) -> EquipmentState:
        """Retourne l'état d'un équipement."""
        if kind not in self._states:
            self._states[kind] = EquipmentState(kind=kind)
        return self._states[kind]

    def set_state(self, kind: EquipmentKind, connected: bool, port_or_device: Optional[str] = None, model_or_label: Optional[str] = None, detected: bool = False) -> None:
        """Met à jour l'état d'un équipement."""
        s = self.get_state(kind)
        s.connected = connected
        s.port_or_device = port_or_device
        s.model_or_label = model_or_label
        s.detected = detected

    def is_connected(self, kind: EquipmentKind) -> bool:
        """Indique si l'équipement est connecté."""
        return self.get_state(kind).connected

    def is_any_connected(self) -> bool:
        """Indique si au moins un équipement du banc est connecté."""
        return any(self.get_state(k).connected for k in bench_equipment_kinds())

    def all_kinds(self) -> list:
        """Ordre des équipements (pour itération)."""
        return bench_equipment_kinds()
