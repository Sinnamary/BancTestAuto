"""
Pastille indicateur de statut (connecté / déconnecté).
Réutilisable pour tout appareil (oscilloscope, multimètre, etc.).
"""
from PyQt6.QtWidgets import QFrame


class StatusIndicator(QFrame):
    """Pastille verte (connecté) ou rouge (déconnecté)."""

    def __init__(self, connected: bool = False, parent=None):
        super().__init__(parent)
        self._connected = connected
        self.setFixedSize(14, 14)
        self._update_style()

    def _update_style(self) -> None:
        color = "#2ecc71" if self._connected else "#e74c3c"
        self.setStyleSheet(f"""
            StatusIndicator {{
                border-radius: 7px;
                background-color: {color};
            }}
        """)

    def set_connected(self, connected: bool) -> None:
        self._connected = connected
        self._update_style()
