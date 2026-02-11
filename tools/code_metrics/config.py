"""Configuration : dossiers analysés, racine du projet."""
from pathlib import Path

# Dossiers de l'application (code source)
APP_DIRS = (
    "config",
    "core",
    "datas",
    "docs",
    "maquette",
    "resources",
    "tests",
    "tools",
    "ui",
)

# Dossiers à ignorer dans l'arborescence
IGNORE_DIRS = {
    "__pycache__", ".venv", "venv", "env", "build", "dist", ".git", "htmlcov",
    "code_metrics_report",  # sortie du rapport pour ne pas l'analyser
}


def get_project_root() -> Path:
    """Racine du projet (parent du dossier tools)."""
    return Path(__file__).resolve().parent.parent.parent
