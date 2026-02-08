"""
Chemins de l'application : racine des ressources et fichier de configuration.
Compatible mode normal (python main.py) et mode frozen (exécutable PyInstaller).
"""
import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    Racine des ressources (config, resources, docs) à lire.
    - Mode frozen (exe) : répertoire temporaire d'extraction PyInstaller (sys._MEIPASS).
    - Mode normal : répertoire racine du projet (parent de core/).
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_config_path() -> Path:
    """
    Chemin du fichier de configuration config.json.
    - Mode frozen : à côté de l'exécutable (pour sauvegarder les réglages).
    - Mode normal : config/config.json à la racine du projet.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config.json"
    return Path(__file__).resolve().parent.parent / "config" / "config.json"
