"""
Visualiseur Bode CSV — module totalement indépendant du banc de test.
Aucune classe ni type partagé avec core ou les autres vues.
Entrée : ouvrir par chemin de fichier CSV uniquement.
"""
from typing import Optional

from PyQt6.QtWidgets import QMessageBox

from .dialog import BodeCsvViewerDialog
from .model import BodeCsvDataset
from .csv_loader import BodeCsvFileLoader


def open_viewer(parent=None, csv_path: str = "", config: Optional[dict] = None) -> None:
    """Point d'entrée unique : charge le CSV et ouvre le dialogue (aucune donnée = message et sortie).
    config: ignoré pour l'instant ; le graphique Bode ouvre avec fond noir par défaut (CDC)."""
    if not csv_path:
        return
    loader = BodeCsvFileLoader()
    dataset = loader.load(csv_path)
    if dataset.is_empty():
        QMessageBox.warning(
            parent or None,
            "CSV Banc filtre",
            "Aucune donnée valide trouvée. Format attendu : f_Hz;Us_V;Us_Ue;Gain_dB (séparateur ;)",
        )
        return
    dlg = BodeCsvViewerDialog(parent, csv_path=csv_path, dataset=dataset, config=config)
    dlg.exec()


__all__ = ["BodeCsvViewerDialog", "open_viewer"]
