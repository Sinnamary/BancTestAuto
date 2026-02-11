#!/usr/bin/env python3
"""
Lance le rapport de métriques de code (tailles, complexité Radon, cohésion, HTML).

À exécuter depuis la racine du projet (de préférence via le lanceur) :

  python run_metrics.py

ou directement :

  python tools/run_metrics_report.py

Options :
  -o, --output DIR   Dossier de sortie (défaut : tools/code_metrics_report)
  --no-cohesion      Ne pas lancer l'analyse de cohésion (package cohesion)
  --no-html          Afficher uniquement dans le terminal (pas de HTML)

Dépendance requise : pip install radon
Optionnel (cohésion) : pip install cohesion
"""
import sys
from pathlib import Path

# S'assurer que le projet est sur le path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Lancer depuis tools/ : le package code_metrics est dans tools/
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from code_metrics.cli import main

if __name__ == "__main__":
    sys.exit(main())
