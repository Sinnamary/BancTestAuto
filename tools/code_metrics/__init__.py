"""
Application de métriques de code : tailles, complexité (Radon), cohésion optionnelle, rapport HTML.
Usage : python tools/run_metrics_report.py [--output dir] [--no-cohesion]
"""
from .config import APP_DIRS, get_project_root
from .collect import collect_files, file_sizes_by_folder, file_sizes_by_extension
from .metrics import compute_file_metrics, compute_cohesion_optional
from .report_html import build_report
from .cli import main

__all__ = [
    "APP_DIRS",
    "get_project_root",
    "collect_files",
    "file_sizes_by_folder",
    "file_sizes_by_extension",
    "compute_file_metrics",
    "compute_cohesion_optional",
    "build_report",
    "main",
]
