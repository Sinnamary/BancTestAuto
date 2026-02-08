"""
Version et métadonnées de l'application — source unique pour le numéro de version.

Mise à jour :
  - Date : si __version_date__ est None ou vide, la date affichée est automatiquement
    celle du jour (à l'exécution). Sinon la date fixée ici est utilisée.
  - Numéro de version : lancer « python bump_version.py patch|minor|major » après une
    modification pour incrémenter et mettre à jour la date dans ce fichier.

Convention : MAJEUR.MINEUR.PATCH (ex. 2.0.0 = changement majeur).
"""
from datetime import date

APP_NAME = "Banc de test automatique"
__version__ = "5.0.0"
__version_date__ = "2026-02-08"


def get_version_date() -> str:
    """Retourne la date de version : __version_date__ si définie, sinon la date du jour."""
    if __version_date__:
        return __version_date__
    return date.today().isoformat()
