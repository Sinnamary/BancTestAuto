#!/usr/bin/env python3
"""
CLI métriques de code : radon (complexité CC, maintenabilité MI, lignes raw).
Génère un résumé terminal + rapport HTML dans tools/code_metrics_report/.
"""
import argparse
import sys
from pathlib import Path

try:
    from radon.complexity import cc_visit
    from radon.raw import analyze
    from radon.metrics import mi_visit
except ImportError:
    print("Erreur : le module 'radon' est requis. Installez-le avec :")
    print("  pip install radon")
    print("  ou : pip install -r tools/requirements-metrics.txt")
    sys.exit(1)


# Dossiers / fichiers exclus du scan (comme .venv, __pycache__)
SKIP_DIRS = {".venv", "__pycache__", ".git", "htmlcov", ".cursor", "build", "dist"}
SKIP_FILES = set()


def collect_py_files(root: Path) -> list[Path]:
    """Collecte les fichiers .py sous root en excluant SKIP_DIRS."""
    out = []
    for path in root.rglob("*.py"):
        if any(part in path.parts for part in SKIP_DIRS):
            continue
        if path.name in SKIP_FILES:
            continue
        try:
            if path.is_file():
                out.append(path)
        except OSError:
            continue
    return sorted(out, key=lambda p: str(p).lower())


def analyze_file(path: Path, root: Path) -> dict | None:
    """Retourne pour un fichier : sloc, lloc, mi, cc_max, cc_total ou None en cas d'erreur."""
    try:
        code = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        raw_mod = analyze(code)
        mi = mi_visit(code, raw_mod.multi)
        cc_results = cc_visit(code)
        cc_max = max((f.complexity for f in cc_results), default=0)
        cc_total = sum(f.complexity for f in cc_results)
        return {
            "path": path,
            "rel": str(path.relative_to(root)),
            "sloc": raw_mod.sloc,
            "lloc": raw_mod.lloc,
            "loc": raw_mod.loc,
            "mi": round(mi, 1),
            "cc_max": cc_max,
            "cc_total": cc_total,
        }
    except Exception:
        return None


def run_scan(root: Path) -> list[dict]:
    """Analyse tous les .py sous root ; retourne liste de dicts par fichier."""
    files = collect_py_files(root)
    results = []
    for path in files:
        data = analyze_file(path, root)
        if data:
            results.append(data)
    return results


def print_terminal_report(results: list[dict], root: Path) -> None:
    """Affiche un résumé par répertoire et par fichier (MI, CC)."""
    if not results:
        print("Aucun fichier Python analysé.")
        return

    # Regrouper par répertoire (premier niveau sous root)
    by_dir = {}
    for r in results:
        rel = r["rel"]
        parts = Path(rel).parts
        dir_name = parts[0] if len(parts) > 1 else "."
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(r)

    total_sloc = sum(r["sloc"] for r in results)
    total_lloc = sum(r["lloc"] for r in results)
    print(f"\nMétriques (radon) — racine : {root}")
    print(f"  Fichiers : {len(results)}  |  SLOC : {total_sloc}  |  LLOC : {total_lloc}")
    print()

    for dir_name in sorted(by_dir.keys(), key=lambda x: (x == ".", x)):
        items = by_dir[dir_name]
        dir_sloc = sum(r["sloc"] for r in items)
        dir_mi_avg = sum(r["mi"] for r in items) / len(items) if items else 0
        print(f"  [{dir_name}]  {len(items)} fichiers  SLOC={dir_sloc}  MI_moy={dir_mi_avg:.1f}")
        for r in sorted(items, key=lambda x: x["rel"]):
            print(f"    {r['rel']:<55}  MI={r['mi']:>5.1f}  CC_max={r['cc_max']:<3}  CC_tot={r['cc_total']:<4}  sloc={r['sloc']}")
    print()


def write_html_report(results: list[dict], output_dir: Path, root: Path) -> None:
    """Écrit index.html dans output_dir avec un tableau des métriques."""
    output_dir.mkdir(parents=True, exist_ok=True)

    rows_html = []
    for r in sorted(results, key=lambda x: x["rel"].lower()):
        rows_html.append(
            f"    <tr><td>{r['rel']}</td><td>{r['sloc']}</td><td>{r['lloc']}</td>"
            f"<td>{r['mi']}</td><td>{r['cc_max']}</td><td>{r['cc_total']}</td></tr>"
        )
    table_body = "\n".join(rows_html)
    total_sloc = sum(r["sloc"] for r in results)
    total_lloc = sum(r["lloc"] for r in results)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Métriques de code — BancTestAuto</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; background: #1e1e1e; color: #d4d4d4; }}
    h1 {{ color: #fff; }}
    table {{ border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border: 1px solid #444; padding: 0.35rem 0.75rem; text-align: left; }}
    th {{ background: #333; color: #fff; }}
    tr:nth-child(even) {{ background: #252525; }}
    .summary {{ margin-bottom: 1rem; color: #888; }}
  </style>
</head>
<body>
  <h1>Métriques de code (radon)</h1>
  <p class="summary">Racine : {root} — {len(results)} fichiers — SLOC : {total_sloc} — LLOC : {total_lloc}</p>
  <table>
    <thead>
      <tr><th>Fichier</th><th>SLOC</th><th>LLOC</th><th>MI</th><th>CC max</th><th>CC total</th></tr>
    </thead>
    <tbody>
{table_body}
    </tbody>
  </table>
</body>
</html>
"""
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rapport de métriques de code (radon : complexité, maintenabilité, lignes)."
    )
    root = Path(__file__).resolve().parent.parent.parent
    default_out = root / "tools" / "code_metrics_report"
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=default_out,
        help=f"Dossier de sortie HTML (défaut : {default_out})",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Ne pas générer le rapport HTML",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=root,
        help="Racine du projet à analyser",
    )
    args = parser.parse_args()
    root = args.path.resolve()

    results = run_scan(root)
    print_terminal_report(results, root)

    if not args.no_html and results:
        write_html_report(results, args.output.resolve(), root)
        print(f"Rapport HTML : {args.output / 'index.html'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
