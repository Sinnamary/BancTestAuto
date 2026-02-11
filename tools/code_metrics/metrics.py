"""Métriques Radon (raw, complexité, maintenabilité) et cohésion optionnelle."""
from pathlib import Path
from typing import Any

from .config import get_project_root

# Structures de sortie
# raw: dict avec loc, lloc, sloc, comments, multi, blank
# cc: liste de {name, type: 'F'|'M'|'C', lineno, endline, complexity, rank}
# mi: float, mi_rank: 'A'|'B'|'C'
# cohesion: dict[class_name, percentage] par fichier


def _read_source(path: Path) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def compute_file_metrics(py_path: Path) -> dict[str, Any] | None:
    """
    Pour un fichier .py : raw (LOC, SLOC), cc (complexité par bloc), mi (indice maintenabilité).
    Retourne None si Radon non disponible ou erreur.
    """
    try:
        from radon.raw import analyze as raw_analyze
        from radon.complexity import cc_visit, cc_rank
        from radon.metrics import mi_visit, mi_rank
    except ImportError:
        return None
    try:
        source = _read_source(py_path)
    except OSError:
        return None
    if not source.strip():
        return {"raw": {"loc": 0, "lloc": 0, "sloc": 0, "comments": 0, "multi": 0, "blank": 0}, "cc": [], "mi": 0.0, "mi_rank": "A"}
    # Raw
    raw = raw_analyze(source)
    raw_dict = {
        "loc": raw.loc,
        "lloc": raw.lloc,
        "sloc": raw.sloc,
        "comments": getattr(raw, "comments", 0) or getattr(raw, "single_comments", 0),
        "multi": raw.multi,
        "blank": raw.blank,
    }
    # Complexité (fonctions et classes avec méthodes)
    blocks = []
    for item in cc_visit(source):
        name = getattr(item, "name", str(item))
        lineno = getattr(item, "lineno", 0)
        endline = getattr(item, "endline", lineno)
        if hasattr(item, "real_complexity"):
            complexity = item.real_complexity  # Class
            kind = "C"
        else:
            complexity = getattr(item, "complexity", 0)
            kind = "M" if getattr(item, "is_method", False) else "F"
        blocks.append({
            "name": name,
            "type": kind,
            "lineno": lineno,
            "endline": endline,
            "complexity": complexity,
            "rank": cc_rank(complexity),
        })
    # Maintainability Index (fichier entier)
    mi_val = mi_visit(source, True)
    return {
        "raw": raw_dict,
        "cc": blocks,
        "mi": round(mi_val, 2),
        "mi_rank": mi_rank(mi_val),
    }


def compute_cohesion_optional(root: Path, py_paths: list[Path]) -> dict[str, dict[str, float]]:
    """
    Si le package 'cohesion' est installé, exécute l'analyse et retourne
    {rel_path: {class_name: cohesion_pct}}. Sinon retourne {}.
    """
    result: dict[str, dict[str, float]] = {}
    try:
        import subprocess
        # cohesion -d dir affiche par fichier/classe un pourcentage
        # On lance cohesion sur chaque répertoire parent des .py pour éviter de tout scanner
        dirs_to_scan = set()
        for p in py_paths:
            try:
                rel = p.relative_to(root)
                if len(rel.parts) > 1:
                    dirs_to_scan.add(rel.parts[0])
                else:
                    dirs_to_scan.add(".")
            except ValueError:
                pass
        for d in dirs_to_scan:
            target = root / d if d != "." else root
            if not target.is_dir():
                continue
            cp = subprocess.run(
                ["cohesion", "-d", str(target), "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(root),
            )
            if cp.returncode != 0 or not cp.stdout.strip():
                # Pas de format JSON ? Essayer sortie texte et parser basique
                cp2 = subprocess.run(
                    ["cohesion", "-d", str(target)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(root),
                )
                if cp2.returncode != 0:
                    continue
                # Format texte typique : "fichier.Classe: 85%"
                for line in cp2.stdout.splitlines():
                    line = line.strip()
                    if ":" in line and "%" in line:
                        part, pct = line.rsplit(":", 1)
                        part = part.strip()
                        pct = pct.strip().replace("%", "").strip()
                        try:
                            pct_f = float(pct)
                            if "." in part:
                                fpath, cls = part.split(".", 1)
                                if fpath.endswith(".py"):
                                    rel = str(Path(fpath).relative_to(root)) if root in Path(fpath).parents else fpath
                                    result.setdefault(rel, {})[cls] = pct_f
                        except (ValueError, TypeError):
                            pass
                continue
            try:
                import json
                data = json.loads(cp.stdout)
                # Structure dépend de cohesion; souvent list of {file, class, cohesion}
                if isinstance(data, list):
                    for ent in data:
                        f = ent.get("file", ent.get("path", ""))
                        cls = ent.get("class", ent.get("name", ""))
                        pct = ent.get("cohesion", ent.get("percentage", 0))
                        if isinstance(pct, str):
                            pct = float(pct.replace("%", ""))
                        try:
                            rel = str(Path(f).relative_to(root))
                        except ValueError:
                            rel = f
                        result.setdefault(rel, {})[cls] = float(pct)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
    except (ImportError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return result
