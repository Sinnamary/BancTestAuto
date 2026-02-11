#!/usr/bin/env python3
"""
Lance le rapport de métriques de code (tailles, complexité Radon, cohésion, HTML).

À exécuter depuis la racine du projet, de préférence en environnement virtuel :

  python run_metrics.py

ou, après activation du venv :

  .venv\\Scripts\\activate   # Windows
  python run_metrics.py

  source .venv/bin/activate  # Linux / macOS
  python run_metrics.py

Rapports : terminal (résumé par extension, dossier, MI/CC par fichier)
           + tools/code_metrics_report/ (HTML).

Dépendance requise : pip install radon
Optionnel (cohésion) : pip install cohesion
"""
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    tools_dir = root / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

    from code_metrics.cli import main as metrics_main

    code = metrics_main()
    if code == 0:
        print()
        print("Rapport HTML : ouvrir tools/code_metrics_report/index.html ou lancer : python serve_metrics.py")
    return code


if __name__ == "__main__":
    sys.exit(main())
