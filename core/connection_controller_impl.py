"""
Implémentation du contrôleur de connexion par délégation (callbacks).
Permet de brancher la logique existante de MainWindow sans déplacer le code.
Pour la future UI à 4 équipements, une autre implémentation gérera les 4 connexions.
"""
from typing import Callable, Optional

from .equipment import EquipmentKind
from .equipment_state import BenchConnectionState


class CallbackConnectionController:
    """
    Contrôleur qui délègue à des callbacks (ex. fournis par MainWindow).
    Utilisable pour l'UI actuelle : connect_all = _reconnect_serial, disconnect_all = fermer les 2 ports,
    get_state = construire BenchConnectionState depuis _multimeter_conn / _generator_conn.
    """

    def __init__(
        self,
        *,
        on_connect_all: Callable[[], None],
        on_disconnect_all: Callable[[], None],
        on_get_state: Callable[[], BenchConnectionState],
        on_apply_config: Optional[Callable[[dict], None]] = None,
    ):
        self._on_connect_all = on_connect_all
        self._on_disconnect_all = on_disconnect_all
        self._on_get_state = on_get_state
        self._on_apply_config = on_apply_config or (lambda _: None)
        self._config: dict = {}

    def apply_config(self, config: dict) -> None:
        self._config = config
        self._on_apply_config(config)

    def connect_all(self) -> None:
        self._on_connect_all()

    def disconnect_all(self) -> None:
        self._on_disconnect_all()

    def get_state(self) -> BenchConnectionState:
        return self._on_get_state()

    def connect(self, kind: EquipmentKind) -> None:
        # Par défaut : connect_all (comportement actuel sans connexion individuelle)
        self.connect_all()

    def disconnect(self, kind: EquipmentKind) -> None:
        # Par défaut : disconnect_all
        self.disconnect_all()
