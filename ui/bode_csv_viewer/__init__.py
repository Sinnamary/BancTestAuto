"""
Visualiseur Bode CSV — module totalement indépendant du banc de test.
Aucune classe ni type partagé avec core ou les autres vues.
Entrée : ouvrir par chemin de fichier CSV uniquement.
"""
from PyQt6.QtWidgets import QMessageBox

from .dialog import BodeCsvViewerDialog
from .model import BodeCsvDataset
from .csv_loader import BodeCsvFileLoader


def open_viewer(parent=None, csv_path: str = "") -> None:
    """Point d'entrée unique : charge le CSV et ouvre le dialogue (aucune donnée = message et sortie)."""
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
    dlg = BodeCsvViewerDialog(parent, csv_path=csv_path, dataset=dataset)
    dlg.exec()


__all__ = ["BodeCsvViewerDialog", "open_viewer"]
