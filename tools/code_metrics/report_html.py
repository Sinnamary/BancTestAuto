"""Génération du rapport HTML (index + page par fichier Python)."""
import html
import re
from pathlib import Path
from typing import Any

from .config import get_project_root


def _rank_class(rank: str, is_mi: bool = False) -> str:
    """Classe CSS pour couleur (A=vert, B=jaune, C/D/E/F=rouge). Pour MI, A=bon, C=mauvais."""
    if is_mi:
        return "rank-a" if rank == "A" else "rank-b" if rank == "B" else "rank-c"
    return "rank-a" if rank in ("A", "B") else "rank-b" if rank in ("C", "D") else "rank-c"


def _safe_id(path: Path, root: Path) -> str:
    """Identifiant HTML safe pour un fichier."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(rel))


def _css() -> str:
    return """
body { font-family: sans-serif; margin: 1rem 2rem; background: #f5f5f5; }
h1 { color: #333; }
h2 { margin-top: 1.5rem; color: #444; }
table { border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 0.4rem 0.8rem; text-align: left; border: 1px solid #ddd; }
th { background: #37474f; color: white; }
tr:nth-child(even) { background: #f9f9f9; }
tr:hover { background: #eee; }
a { color: #1565c0; }
.rank-a { color: #2e7d32; font-weight: bold; }
.rank-b { color: #f9a825; font-weight: bold; }
.rank-c { color: #c62828; font-weight: bold; }
.summary { display: flex; flex-wrap: wrap; gap: 1rem; margin: 1rem 0; }
.summary .card { background: white; padding: 1rem 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 120px; }
.summary .card .value { font-size: 1.5rem; color: #1565c0; }
.nav { margin: 1rem 0; }
"""


def _build_index(
    root: Path,
    files: list[Path],
    by_ext: list[tuple[str, int, int]],
    by_folder: list[tuple[str, int, int]],
    py_files: list[Path],
    file_metrics: dict[Path, dict],
    total_bytes: int,
    py_lines: int,
    cohesion: dict[str, dict[str, float]],
    out_dir: Path,
) -> None:
    index = out_dir / "index.html"
    py_count = len(py_files)
    total_files = len(files)

    rows = []
    for p in sorted(py_files, key=lambda x: str(x)):
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        rel_str = str(rel).replace("\\", "/")
        size_b = p.stat().st_size
        m = file_metrics.get(p)
        if m:
            loc = m["raw"]["loc"]
            sloc = m["raw"]["sloc"]
            mi = m["mi"]
            mi_r = m["mi_rank"]
            cc_max = max((b["complexity"] for b in m["cc"]), default=0)
        else:
            loc = sloc = mi = cc_max = 0
            mi_r = "-"
        file_id = _safe_id(p, root)
        mi_class = _rank_class(mi_r, is_mi=True)
        rows.append(
            f"<tr><td><a href=\"{file_id}.html\">{html.escape(rel_str)}</a></td>"
            f"<td>{size_b}</td><td>{loc}</td><td>{sloc}</td>"
            f"<td class=\"{mi_class}\">{mi} ({mi_r})</td><td>{cc_max}</td></tr>"
        )

    by_ext_rows = "".join(
        f"<tr><td>{html.escape(ext)}</td><td>{c}</td><td>{s}</td><td>{s/1024:.1f}</td></tr>"
        for ext, c, s in by_ext
    )
    by_folder_rows = "".join(
        f"<tr><td>{html.escape(folder)}</td><td>{c}</td><td>{s}</td><td>{s/1024:.1f}</td></tr>"
        for folder, c, s in by_folder
    )

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Métriques de code - BancTestAuto</title>
<style>{_css()}</style>
</head>
<body>
<h1>Rapport de métriques de code</h1>
<div class="summary">
  <div class="card"><span class="value">{total_files}</span><br>Fichiers</div>
  <div class="card"><span class="value">{py_count}</span><br>Fichiers Python</div>
  <div class="card"><span class="value">{py_lines}</span><br>Lignes Python</div>
  <div class="card"><span class="value">{total_bytes/1024:.1f} KB</span><br>Taille totale</div>
</div>

<h2>Par extension</h2>
<table>
<thead><tr><th>Extension</th><th>Nombre</th><th>Octets</th><th>KB</th></tr></thead>
<tbody>{by_ext_rows}</tbody>
</table>

<h2>Par dossier</h2>
<table>
<thead><tr><th>Dossier</th><th>Fichiers</th><th>Octets</th><th>KB</th></tr></thead>
<tbody>{by_folder_rows}</tbody>
</table>

<h2>Fichiers Python (détail)</h2>
<table>
<thead><tr><th>Fichier</th><th>Octets</th><th>LOC</th><th>SLOC</th><th>MI (rang)</th><th>CC max</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</body>
</html>
"""
    index.write_text(html_content, encoding="utf-8")


def _build_file_page(
    py_path: Path,
    root: Path,
    metrics: dict[str, Any],
    cohesion_classes: dict[str, float],
    out_dir: Path,
) -> None:
    try:
        rel = py_path.relative_to(root)
    except ValueError:
        rel = py_path
    rel_str = str(rel).replace("\\", "/")
    file_id = _safe_id(py_path, root)
    size_b = py_path.stat().st_size

    raw = metrics.get("raw", {})
    loc = raw.get("loc", 0)
    sloc = raw.get("sloc", 0)
    mi = metrics.get("mi", 0)
    mi_rank = metrics.get("mi_rank", "-")
    mi_class = _rank_class(mi_rank, is_mi=True)

    blocks_rows = []
    for b in metrics.get("cc", []):
        kind = b.get("type", "F")
        kind_label = {"F": "Fonction", "M": "Méthode", "C": "Classe"}.get(kind, kind)
        name = html.escape(b.get("name", ""))
        ln = b.get("lineno", 0)
        en = b.get("endline", ln)
        lines = en - ln + 1 if en >= ln else 0
        cc = b.get("complexity", 0)
        rank = b.get("rank", "A")
        rclass = _rank_class(rank, is_mi=False)
        coh = ""
        if name in cohesion_classes:
            coh = f" <span class=\"rank-a\">({cohesion_classes[name]:.0f}% cohésion)</span>"
        blocks_rows.append(
            f"<tr><td>{kind_label}</td><td>{name}</td><td>{ln}</td><td>{lines}</td>"
            f"<td class=\"{rclass}\">{cc} ({rank})</td><td>{coh}</td></tr>"
        )
    blocks_body = "".join(blocks_rows) if blocks_rows else "<tr><td colspan=\"6\">Aucun bloc (fichier vide ou non analysé)</td></tr>"

    back_link = '<a href="index.html">← Retour à l\'index</a>'
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{html.escape(rel_str)} - Métriques</title>
<style>{_css()}</style>
</head>
<body>
<div class="nav">{back_link}</div>
<h1>{html.escape(rel_str)}</h1>
<div class="summary">
  <div class="card">Taille <span class="value">{size_b}</span> octets</div>
  <div class="card">LOC <span class="value">{loc}</span></div>
  <div class="card">SLOC <span class="value">{sloc}</span></div>
  <div class="card">Maintenabilité <span class="value {mi_class}\">{mi} ({mi_rank})</span></div>
</div>
<h2>Détail raw</h2>
<p>Commentaires: {raw.get('comments', 0)}, Multi-lignes: {raw.get('multi', 0)}, Blank: {raw.get('blank', 0)}.</p>
<h2>Blocs (fonctions, méthodes, classes)</h2>
<table>
<thead><tr><th>Type</th><th>Nom</th><th>Ligne</th><th>Lignes</th><th>Complexité (rang)</th><th>Cohésion</th></tr></thead>
<tbody>{blocks_body}</tbody>
</table>
</body>
</html>
"""
    (out_dir / f"{file_id}.html").write_text(html_content, encoding="utf-8")


def build_report(
    out_dir: Path | str | None = None,
    include_cohesion: bool = True,
    root: Path | None = None,
) -> Path:
    """
    Construit le rapport HTML dans out_dir (défaut: tools/code_metrics_report).
    Retourne le chemin du dossier de sortie.
    """
    if root is None:
        root = get_project_root()
    out_dir = Path(out_dir) if out_dir else root / "tools" / "code_metrics_report"
    out_dir.mkdir(parents=True, exist_ok=True)

    from . import collect
    from . import metrics

    files = collect.collect_files(root)
    if not files:
        return out_dir

    by_ext = collect.file_sizes_by_extension(files, root)
    by_folder = collect.file_sizes_by_folder(files, root)
    total_bytes = sum(f.stat().st_size for f in files)
    py_files = [f for f in files if f.suffix == ".py"]
    py_lines = sum(
        sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
        for f in py_files
    )

    file_metrics: dict[Path, dict] = {}
    for p in py_files:
        m = metrics.compute_file_metrics(p)
        if m:
            file_metrics[p] = m

    cohesion: dict[str, dict[str, float]] = {}
    if include_cohesion and py_files:
        cohesion = metrics.compute_cohesion_optional(root, py_files)

    _build_index(
        root, files, by_ext, by_folder, py_files,
        file_metrics, total_bytes, py_lines, cohesion, out_dir,
    )
    for p in py_files:
        m = file_metrics.get(p)
        if not m:
            m = {"raw": {"loc": 0, "lloc": 0, "sloc": 0, "comments": 0, "multi": 0, "blank": 0}, "cc": [], "mi": 0.0, "mi_rank": "A"}
        try:
            rel = p.relative_to(root)
        except ValueError:
            rel = p
        rel_str = str(rel).replace("\\", "/")
        cohesion_classes = cohesion.get(rel_str, cohesion.get(str(rel), {}))
        _build_file_page(p, root, m, cohesion_classes, out_dir)

    return out_dir
