#!/usr/bin/env python3
"""
Lance les tests avec couverture de code (pytest-cov).

À exécuter depuis la racine du projet, de préférence en environnement virtuel :

  python run_coverage.py

ou, après activation du venv :

  .venv\\Scripts\\activate   # Windows
  python run_coverage.py

  source .venv/bin/activate  # Linux / macOS
  python run_coverage.py

Modules couverts : config, core, ui.bode_csv_viewer.
Rapports : terminal (lignes manquantes) + htmlcov/ (HTML).
"""
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-v",
        "--tb=short",
        "--cov=config",
        "--cov=core",
        "--cov=ui.bode_csv_viewer",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--no-cov-on-fail",
    ]

    result = subprocess.run(cmd, cwd=str(root))
    if result.returncode == 0:
        print()
        print("Rapport HTML : ouvrir htmlcov/index.html ou lancer : python serve_htmlcov.py")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
