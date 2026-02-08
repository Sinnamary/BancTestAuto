#!/usr/bin/env python3
"""
Script de construction de l'exécutable BancTestAuto avec PyInstaller.

À lancer depuis la racine du projet, avec l'environnement virtuel activé :

  # Windows (PowerShell)
  .\.venv\Scripts\Activate.ps1
  python build_exe.py

  # Linux / macOS
  source .venv/bin/activate
  python build_exe.py

L'exécutable est généré dans dist/BancTestAuto.exe (ou dist/BancTestAuto sous Linux).

Prérequis : pip install pyinstaller (dans le venv).
"""
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent

    if not (root / "BancTestAuto.spec").exists():
        print("Erreur : BancTestAuto.spec introuvable. Lancez ce script depuis la racine du projet.")
        sys.exit(1)

    if not (root / "main.py").exists():
        print("Erreur : main.py introuvable. Lancez ce script depuis la racine du projet.")
        sys.exit(1)

    # Utiliser l'interpréteur courant (celui du venv si activé) pour PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "BancTestAuto.spec"]

    print("Construction de l'exécutable avec PyInstaller...")
    print(f"  Python : {sys.executable}")
    print(f"  Répertoire : {root}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            check=False,
        )
    except FileNotFoundError:
        print("Erreur : PyInstaller introuvable. Installez-le dans l'environnement virtuel :")
        print("  pip install pyinstaller")
        sys.exit(1)

    if result.returncode != 0:
        sys.exit(result.returncode)

    exe_name = "BancTestAuto.exe" if sys.platform == "win32" else "BancTestAuto"
    exe_path = root / "dist" / exe_name
    if exe_path.exists():
        print()
        print(f"Exécutable créé : {exe_path}")
    else:
        print()
        print("Build terminé. Vérifiez le dossier dist/.")


if __name__ == "__main__":
    main()
