"""
Types d'équipement du banc de test.
Un seul endroit pour les identifiants, noms d'affichage et clés de configuration.
"""
from enum import Enum
from typing import List


class EquipmentKind(str, Enum):
    """Identifiants des équipements du banc."""
    MULTIMETER = "multimeter"
    GENERATOR = "generator"
    POWER_SUPPLY = "power_supply"
    OSCILLOSCOPE = "oscilloscope"


# Correspondance kind → clé dans config.json
CONFIG_KEYS: dict[EquipmentKind, str] = {
    EquipmentKind.MULTIMETER: "serial_multimeter",
    EquipmentKind.GENERATOR: "serial_generator",
    EquipmentKind.POWER_SUPPLY: "serial_power_supply",
    EquipmentKind.OSCILLOSCOPE: "usb_oscilloscope",
}

# Correspondance kind → libellé affiché
DISPLAY_NAMES: dict[EquipmentKind, str] = {
    EquipmentKind.MULTIMETER: "Multimètre",
    EquipmentKind.GENERATOR: "Générateur",
    EquipmentKind.POWER_SUPPLY: "Alimentation",
    EquipmentKind.OSCILLOSCOPE: "Oscilloscope",
}


def equipment_display_name(kind: EquipmentKind) -> str:
    """Retourne le libellé d'affichage pour un type d'équipement."""
    return DISPLAY_NAMES.get(kind, kind.value)


def equipment_config_key(kind: EquipmentKind) -> str:
    """Retourne la clé de section config (serial_*, usb_*) pour ce type."""
    return CONFIG_KEYS.get(kind, "")


def bench_equipment_kinds() -> List[EquipmentKind]:
    """Retourne la liste des équipements du banc (ordre d'affichage)."""
    return [
        EquipmentKind.MULTIMETER,
        EquipmentKind.GENERATOR,
        EquipmentKind.POWER_SUPPLY,
        EquipmentKind.OSCILLOSCOPE,
    ]
