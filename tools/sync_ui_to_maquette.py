#!/usr/bin/env python3
"""
Synchronise l'UI du programme principal vers la maquette.
Copie récursivement ui/ vers maquette/ui/ (écrase les fichiers existants).
À lancer depuis la racine du projet : python tools/sync_ui_to_maquette.py

La synchronisation dans l'autre sens (maquette → programme principal) se fait à la main
après validation des changements dans la maquette.
"""
import shutil
import sys
from pathlib import Path

# Racine du projet = répertoire contenant ui/ et maquette/
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SOURCE_UI = PROJECT_ROOT / "ui"
TARGET_UI = PROJECT_ROOT / "maquette" / "ui"

# Répertoires à ne pas copier
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def should_skip(path: Path) -> bool:
    if path.name in SKIP_DIRS:
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    return False


def sync_ui_to_maquette() -> int:
    if not SOURCE_UI.is_dir():
        print(f"Erreur : répertoire source introuvable : {SOURCE_UI}", file=sys.stderr)
        return 1
    if not (PROJECT_ROOT / "maquette").is_dir():
        print(f"Erreur : répertoire maquette introuvable : {PROJECT_ROOT / 'maquette'}", file=sys.stderr)
        return 1

    target_parent = TARGET_UI.parent
    target_parent.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src in sorted(SOURCE_UI.rglob("*")):
        if should_skip(src):
            continue
        rel = src.relative_to(SOURCE_UI)
        dst = TARGET_UI / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        if src.is_file():
            shutil.copy2(src, dst)
            copied += 1
            print(f"  {rel}")

    print(f"\nSync terminée : {copied} fichier(s) copié(s) de ui/ vers maquette/ui/")
    return 0


if __name__ == "__main__":
    print(f"Source : {SOURCE_UI}")
    print(f"Cible  : {TARGET_UI}\n")
    sys.exit(sync_ui_to_maquette())
