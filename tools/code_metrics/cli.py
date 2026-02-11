"""Point d'entrée en ligne de commande."""
import argparse
import sys
from pathlib import Path

from .config import APP_DIRS, get_project_root
from .collect import (
    collect_files,
    file_sizes_by_extension,
    file_sizes_by_folder,
    count_py_lines,
)
from .report_html import build_report
from .metrics import compute_file_metrics, compute_cohesion_optional


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rapport de métriques de code : tailles, complexité (Radon), cohésion, HTML."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Dossier de sortie du rapport HTML (défaut: tools/code_metrics_report)",
    )
    parser.add_argument(
        "--no-cohesion",
        action="store_true",
        help="Ne pas tenter d'exécuter l'analyse de cohésion (cohesion)",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Ne pas générer le rapport HTML (affichage terminal uniquement)",
    )
    args = parser.parse_args()

    root = get_project_root()
    files = collect_files(root)
    if not files:
        print("Aucun fichier trouvé.")
        return 0

    # Vérifier Radon
    try:
        from radon.raw import analyze  # noqa: F401
    except ImportError:
        print("Erreur: le package 'radon' est requis. Installez-le avec: pip install radon")
        return 1

    by_ext = file_sizes_by_extension(files, root)
    by_folder = file_sizes_by_folder(files, root)
    total_bytes = sum(f.stat().st_size for f in files)
    py_files = [f for f in files if f.suffix == ".py"]
    py_count = len(py_files)
    py_lines = count_py_lines(py_files)

    # Affichage terminal
    print("Métriques de code (dossiers: " + ", ".join(APP_DIRS) + " + racine)\n")
    print("--- Par extension ---")
    for ext, count, size in by_ext[:15]:
        print(f"  {ext:<20} {count:>5} fichiers   {size/1024:>8.1f} KB")
    print("\n--- Par dossier ---")
    for folder, count, size in by_folder:
        print(f"  {folder:<20} {count:>5} fichiers   {size/1024:>8.1f} KB")
    print(f"\n--- Résumé ---")
    print(f"  Fichiers totaux : {len(files)}")
    print(f"  Fichiers Python : {py_count}")
    print(f"  Lignes Python   : {py_lines}")
    print(f"  Taille totale   : {total_bytes/1024:.1f} KB")

    # Métriques Radon par fichier (résumé)
    print("\n--- Complexité (fichiers Python) ---")
    file_metrics = {}
    for p in sorted(py_files, key=lambda x: str(x)):
        m = compute_file_metrics(p)
        if m:
            file_metrics[p] = m
            try:
                rel = p.relative_to(root)
            except ValueError:
                rel = p
            cc_max = max((b["complexity"] for b in m["cc"]), default=0)
            print(f"  {rel}  MI={m['mi']} ({m['mi_rank']})  CC_max={cc_max}  LOC={m['raw']['loc']}")

    if not args.no_html:
        out_dir = build_report(
            out_dir=args.output,
            include_cohesion=not args.no_cohesion,
            root=root,
        )
        print(f"\nRapport HTML généré : {out_dir / 'index.html'}")
        print("Ouvrir dans un navigateur ou lancer un serveur (ex: python -m http.server --directory tools/code_metrics_report).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
