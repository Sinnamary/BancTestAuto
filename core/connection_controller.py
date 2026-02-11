"""
Interface du contrôleur de connexion du banc.
L'UI (actuelle ou future) ne dépend que de cette interface pour connecter/déconnecter
et lire l'état ; l'implémentation peut déléguer à MainWindow ou gérer les 4 équipements.
"""
from typing import Protocol

from .equipment import EquipmentKind
from .equipment_state import BenchConnectionState


class ConnectionController(Protocol):
    """
    Contrôleur de connexion : connect_all, disconnect_all, état du banc.
    apply_config() met à jour la config utilisée pour les prochains connect_all().
    """

    def get_state(self) -> BenchConnectionState:
        """Retourne l'état actuel de connexion de chaque équipement."""
        ...

    def connect_all(self) -> None:
        """Tente de connecter tous les équipements configurés."""
        ...

    def disconnect_all(self) -> None:
        """Ferme toutes les connexions des équipements du banc."""
        ...

    def apply_config(self, config: dict) -> None:
        """Met à jour la configuration (ports, débits, etc.) pour les prochaines connexions."""
        ...

    def connect(self, kind: EquipmentKind) -> None:
        """Connecte un seul équipement (optionnel)."""
        ...

    def disconnect(self, kind: EquipmentKind) -> None:
        """Déconnecte un seul équipement (optionnel)."""
        ...
