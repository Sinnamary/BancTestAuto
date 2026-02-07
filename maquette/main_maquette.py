"""
Point d'entrée de la maquette interface.
Lance uniquement l'interface PyQt6, sans logique métier (pas de core/, pas de config).
Lancer depuis la racine du projet : python maquette/main_maquette.py
"""
import sys
from pathlib import Path

# Rendre le répertoire maquette/ importable pour "from ui.xxx"
_maquette_dir = Path(__file__).resolve().parent
if str(_maquette_dir) not in sys.path:
    sys.path.insert(0, str(_maquette_dir))

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Banc de test automatique — Maquette")
    main_win = MainWindow()
    main_win.setMinimumSize(900, 700)
    main_win.resize(1000, 750)
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
