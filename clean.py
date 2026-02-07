#!/usr/bin/env python3
"""
Nettoyage du projet : __pycache__/, fichiers dans logs/, optionnellement htmlcov/.
Usage : python clean.py [--all]
  --all : supprime aussi htmlcov/ (rapport de couverture pytest).
"""
import argparse
import shutil
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Nettoyage __pycache__, logs, optionnel htmlcov")
    parser.add_argument("--all", action="store_true", help="Supprimer aussi htmlcov/")
    args = parser.parse_args()

    removed = []

    # Ne pas toucher au venv (éviter de casser les paquets installés)
    skip_dirs = {root / ".venv", root / "venv", root / "env"}

    # 1. __pycache__ (hors .venv)
    for d in root.rglob("__pycache__"):
        if not d.is_dir():
            continue
        if any(skip in d.parents for skip in skip_dirs):
            continue
        shutil.rmtree(d, ignore_errors=True)
        removed.append(str(d.relative_to(root)))

    # 2. Fichiers dans logs/
    logs_dir = root / "logs"
    if logs_dir.is_dir():
        for f in logs_dir.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                    removed.append(str(f.relative_to(root)))
                except OSError:
                    pass

    # 3. Optionnel : htmlcov/
    if args.all:
        htmlcov = root / "htmlcov"
        if htmlcov.is_dir():
            shutil.rmtree(htmlcov, ignore_errors=True)
            removed.append("htmlcov/")

    for p in removed:
        print("Supprimé:", p)
    if not removed:
        print("Rien à supprimer.")
    else:
        print(f"Total : {len(removed)} élément(s).")


if __name__ == "__main__":
    main()
