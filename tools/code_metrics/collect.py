"""Collecte des fichiers et calcul des tailles (octets, lignes)."""
from pathlib import Path

from .config import APP_DIRS, IGNORE_DIRS, get_project_root


def get_root() -> Path:
    return get_project_root()


def collect_files(root: Path | None = None) -> list[Path]:
    """Collecte tous les fichiers du code source (hors __pycache__, .venv, etc.)."""
    if root is None:
        root = get_root()
    files: list[Path] = []
    for f in root.iterdir():
        if f.name.startswith(".") and f.is_dir():
            continue
        if f.is_file():
            files.append(f)
    for dir_name in APP_DIRS:
        dir_path = root / dir_name
        if not dir_path.is_dir():
            continue
        for f in dir_path.rglob("*"):
            if not f.is_file():
                continue
            if any(ign in f.parts for ign in IGNORE_DIRS):
                continue
            files.append(f)
    return files


def file_sizes_by_extension(files: list[Path], root: Path | None = None) -> list[tuple[str, int, int]]:
    """(extension, count, size_bytes) trié par taille décroissante."""
    if root is None:
        root = get_root()
    by_ext: dict[str, list[Path]] = {}
    for f in files:
        ext = f.suffix if f.suffix else "(sans extension)"
        by_ext.setdefault(ext, []).append(f)
    out = [(ext, len(paths), sum(p.stat().st_size for p in paths)) for ext, paths in by_ext.items()]
    out.sort(key=lambda x: x[2], reverse=True)
    return out


def file_sizes_by_folder(files: list[Path], root: Path | None = None) -> list[tuple[str, int, int]]:
    """(dossier, count, size_bytes). Dossier = premier niveau ou '(racine)'."""
    if root is None:
        root = get_root()
    by_folder: dict[str, list[Path]] = {"(racine)": []}
    for f in files:
        try:
            rel = f.relative_to(root)
            parts = rel.parts
            if len(parts) == 1:
                by_folder["(racine)"].append(f)
            else:
                by_folder.setdefault(parts[0], []).append(f)
        except ValueError:
            by_folder["(racine)"].append(f)
    out = [(folder, len(paths), sum(p.stat().st_size for p in paths)) for folder, paths in by_folder.items()]
    out.sort(key=lambda x: x[2], reverse=True)
    return out


def count_py_lines(files: list[Path]) -> int:
    """Compte les lignes des fichiers .py (approximation)."""
    total = 0
    for f in files:
        if f.suffix != ".py":
            continue
        try:
            total += sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return total
