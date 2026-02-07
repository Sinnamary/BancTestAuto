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

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Banc de test automatique")
    main_win = MainWindow()
    main_win.setMinimumSize(900, 700)
    main_win.resize(1000, 750)
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
