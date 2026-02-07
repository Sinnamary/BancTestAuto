"""
Point d'entrée de l'application Banc de test automatique.
Charge la config, lance la fenêtre principale avec connexions série et banc filtre.
"""
import sys
from pathlib import Path

# Racine du projet = répertoire parent de main.py
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from PyQt6.QtWidgets import QApplication

from config.settings import load_config
from core.app_logger import init_app_logging
from ui.main_window import MainWindow
from ui.theme_loader import get_theme_stylesheet


def main():
    config = load_config()
    init_app_logging(config)

    app = QApplication(sys.argv)
    app.setApplicationName("Banc de test automatique")

    # Thème : config display.theme (dark / light)
    theme = (config.get("display") or {}).get("theme", "dark")
    stylesheet = get_theme_stylesheet(theme)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    main_win = MainWindow()
    main_win.setMinimumSize(900, 700)
    main_win.resize(1000, 750)
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
