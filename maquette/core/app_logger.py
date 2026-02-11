"""
Stub logger pour la maquette : get_logger retourne un logger standard, pas de fichier.
"""
import logging
from pathlib import Path
from typing import Any, Optional

LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}


def init_app_logging(config: dict[str, Any]) -> None:
    """No-op en maquette."""
    pass


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def set_level(level_name: str) -> None:
    level = LEVELS.get(str(level_name).upper(), logging.INFO)
    logging.getLogger().setLevel(level)


def get_current_level_name() -> str:
    return "INFO"


def get_latest_log_path(config: dict[str, Any]) -> Optional[Path]:
    return None
