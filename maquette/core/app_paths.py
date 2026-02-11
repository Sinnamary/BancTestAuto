"""
Stub : chemins. get_base_path() = racine du projet pour charger resources/themes.
"""
from pathlib import Path

_maquette_dir = Path(__file__).resolve().parent.parent
_project_root = _maquette_dir.parent


def get_base_path() -> Path:
    """Racine du projet (pour resources/themes, etc.)."""
    return _project_root


def get_config_path() -> Path:
    """Chemin config.json (factice en maquette)."""
    return _project_root / "config" / "config.json"
