"""
Point d'entrée de la maquette interface.
Lance l'UI du programme principal (copiée dans maquette/ui/) avec les stubs config/core :
pas de logique métier, pas de ports série. Lancer depuis la racine du projet :
  python maquette/main_maquette.py
Synchronisation UI programme → maquette : python tools/sync_ui_to_maquette.py
"""
import sys
from pathlib import Path

# Maquette en premier pour que config/core/ui soient ceux de la maquette
_maquette_dir = Path(__file__).resolve().parent
_project_root = _maquette_dir.parent
if str(_maquette_dir) not in sys.path:
    sys.path.insert(0, str(_maquette_dir))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme_loader import get_theme_stylesheet


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Banc de test automatique — Maquette")

    # Config factice (stub) pour thème et police
    from config.settings import load_config
    config = load_config()
    display = config.get("display") or {}
    font_family = (display.get("font_family") or "").strip() or "Segoe UI"
    if font_family:
        app.setFont(QFont(font_family, 10))
    theme = display.get("theme", "dark")
    stylesheet = get_theme_stylesheet(theme, font_family=font_family)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    main_win = MainWindow()
    main_win.setMinimumSize(900, 700)
    main_win.resize(1000, 750)
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
