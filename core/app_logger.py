"""
Log global de l'application : un fichier par lancement, niveau (DEBUG, INFO, etc.) depuis config.json.

Utilisation dans les modules :
    from core.app_logger import get_logger
    logger = get_logger(__name__)
    logger.debug("détail technique")
    logger.info("information")
    logger.warning("avertissement")
    logger.error("erreur")

Le niveau (DEBUG, INFO, WARNING, ERROR) est lu dans config.json, section "logging", clé "level".
Fichiers générés dans logging.output_dir :
  - app_YYYY-MM-DD_HH-MM-SS.log : log général (démarrage, détection, connexions, erreurs).
  - serial_YYYY-MM-DD_HH-MM-SS.log : log des échanges de l’onglet Terminal série uniquement (TX/RX),
    avec l’équipement connecté indiqué une fois au début du choix. Créé au premier choix d’équipement ou premier envoi/réception.

En mode DEBUG, l'application enregistre en plus : commandes série envoyées/reçues (port, débit, données),
commandes FY6900 et SCPI (TX/RX), détection des appareils (étape par étape), trames Modbus RS305P,
et chaque point du balayage banc filtre (fréquence, mesure, gain).
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

_initialized = False
_file_handler = None

# Niveaux valides dans le JSON
LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}


def _level_from_config(config: dict[str, Any]) -> int:
    level_name = (config.get("logging") or {}).get("level", "INFO")
    return LEVELS.get(str(level_name).upper(), logging.INFO)


def init_app_logging(config: dict[str, Any]) -> None:
    """
    Initialise le log global : crée un fichier horodaté dans logging.output_dir,
    applique le niveau depuis config.logging.level, attache le handler au logger racine.
    À appeler une fois au démarrage (ex. depuis main.py après chargement de la config).
    """
    global _initialized, _file_handler
    if _initialized:
        return

    log_cfg = config.get("logging") or {}
    output_dir = Path(log_cfg.get("output_dir", "./logs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    log_path = output_dir / f"app_{now:%Y-%m-%d_%H-%M-%S}.log"

    level = _level_from_config(config)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _file_handler = logging.FileHandler(log_path, encoding="utf-8")
    _file_handler.setLevel(level)
    _file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(_file_handler)

    _initialized = True
    root.info("Log initialisé — niveau=%s — fichier=%s", logging.getLevelName(level), log_path)


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger pour le module (ex. __name__).
    Utiliser après init_app_logging(config).
    """
    return logging.getLogger(name)


def set_level(level_name: str) -> None:
    """
    Change le niveau de log à la volée (ex. depuis le menu Configuration).
    level_name : "DEBUG", "INFO", "WARNING", "ERROR"
    """
    global _file_handler
    level = LEVELS.get(str(level_name).upper(), logging.INFO)
    if _file_handler is not None:
        _file_handler.setLevel(level)
    logging.getLogger().setLevel(level)


def get_current_level_name() -> str:
    """Retourne le nom du niveau actuel (ex. "INFO")."""
    if _file_handler is None:
        return "INFO"
    level = _file_handler.level
    for name, value in LEVELS.items():
        if value == level:
            return name
    return "INFO"


def get_latest_log_path(config: dict[str, Any]) -> Optional[Path]:
    """
    Retourne le chemin du fichier de log le plus récent (app_*.log) dans le répertoire
    configuré (logging.output_dir). Retourne None si aucun fichier ou répertoire absent.
    """
    log_cfg = config.get("logging") or {}
    output_dir = Path(log_cfg.get("output_dir", "./logs"))
    if not output_dir.exists():
        return None
    logs = list(output_dir.glob("app_*.log"))
    if not logs:
        return None
    return max(logs, key=lambda p: p.stat().st_mtime)
