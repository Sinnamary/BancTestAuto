"""
Charge les feuilles de style (QSS) des thèmes depuis resources/themes/.
Permet d'appliquer un thème sombre ou clair à l'application.
Compatible exécutable PyInstaller (ressources dans sys._MEIPASS).
"""
from pathlib import Path

from core.app_paths import get_base_path


def get_resources_themes_dir(base_path: Path | None = None) -> Path:
    """Retourne le répertoire resources/themes (par défaut : racine projet ou MEIPASS si exe)."""
    if base_path is None:
        base_path = get_base_path()
    return base_path / "resources" / "themes"


def get_theme_stylesheet(theme_name: str, base_path: Path | None = None) -> str:
    """
    Charge le contenu du fichier QSS du thème (ex. dark.qss, light.qss).
    Retourne une chaîne vide si le fichier n'existe pas ou theme_name est vide.
    """
    if not theme_name or not theme_name.strip():
        return ""
    theme_name = theme_name.strip().lower()
    # Noms de fichier sécurisés : uniquement [a-z0-9_]
    safe_name = "".join(c for c in theme_name if c.isalnum() or c == "_")
    if not safe_name:
        return ""
    themes_dir = get_resources_themes_dir(base_path)
    path = themes_dir / f"{safe_name}.qss"
    if not path.is_file():
        return ""
    try:
        content = path.read_text(encoding="utf-8")
        # Chemin absolu du dossier themes (slashes) pour les SVG spinbox — pas de file://
        # pour éviter que Qt concatène avec le CWD (ex. CWD + "file:/C:/..." → chemin invalide)
        try:
            theme_dir_path = str(themes_dir.resolve()).replace("\\", "/") + "/"
        except Exception:
            theme_dir_path = ""
        if theme_dir_path and "{{THEME_DIR}}" in content:
            content = content.replace("{{THEME_DIR}}", theme_dir_path)
        return content
    except OSError:
        return ""
