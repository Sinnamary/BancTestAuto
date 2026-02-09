"""
Point d'entrée de l'application Banc de test automatique.
Charge la config, lance la fenêtre principale avec connexions série et banc filtre.
Compatible exécutable PyInstaller : config et logs à côté du .exe.
"""
import sys
from pathlib import Path

# Racine du projet = répertoire parent de main.py (ou répertoire de l'exe si frozen)
if getattr(sys, "frozen", False):
    _root = Path(sys.executable).resolve().parent
    # Répertoire de travail = répertoire de l'exe (pour config.json, ./logs, etc.)
    import os
    os.chdir(_root)
else:
    _root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplicationgit

from config.settings import load_config
from core.app_logger import init_app_logging
from ui.main_window import MainWindow
from ui.theme_loader import get_theme_stylesheet


def main():
    config = load_config()
    init_app_logging(config)

    app = QApplication(sys.argv)
    app.setApplicationName("Banc de test automatique")

    # Police et thème depuis la config (display.font_family, display.theme)
    display = config.get("display") or {}
    font_family = (display.get("font_family") or "").strip()
    if not font_family and sys.platform == "win32":
        font_family = "Segoe UI"  # évite erreurs DirectWrite avec MS Sans Serif
    if font_family:
        app.setFont(QFont(font_family, 10))

    theme = display.get("theme", "dark")
    stylesheet = get_theme_stylesheet(theme, font_family=font_family or "Segoe UI, Arial, sans-serif")
    if stylesheet:
        app.setStyleSheet(stylesheet)

    main_win = MainWindow()
    main_win.setMinimumSize(900, 700)
    main_win.resize(1000, 750)
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
