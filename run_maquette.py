"""
Lanceur optionnel de la maquette interface (depuis la racine du projet).
Équivalent à : python maquette/main_maquette.py
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    script = root / "maquette" / "main_maquette.py"
    sys.exit(subprocess.call([sys.executable, str(script)], cwd=str(root)))
