"""
Dialogue de configuration série : port, débit, timeouts, log.
Pour multimètre et/ou générateur ; charge et retourne les sections config.

UI_CHANGES_VIA_MAQUETTE: Évolution vers 4 équipements (onglets ou formulaire Alimentation,
Oscilloscope) → concevoir dans la maquette, puis reporter. Voir docs/DEVELOPPEMENT.md.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QTabWidget,
    QLabel,
)

from .serial_form import SerialConfigForm


class SerialConfigDialog(QDialog):
    def __init__(self, config: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration série")
        self._config = config or {}
        baud_opts = self._config.get("limits", {}).get("baudrate_options", SerialConfigForm.DEFAULT_BAUDRATES)

        layout = QVBoxLayout(self)
        hint = QLabel("Valeurs lues depuis config.json. OK = appliquer et reconnecter ; Fichier → Sauvegarder config pour enregistrer.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(hint)
        self._tabs = QTabWidget()

        self._form_multimeter = SerialConfigForm(self._config.get("serial_multimeter", {}), baud_opts)
        self._tabs.addTab(self._form_multimeter.widget(), "Multimètre")

        self._form_generator = SerialConfigForm(self._config.get("serial_generator", {}), baud_opts)
        self._tabs.addTab(self._form_generator.widget(), "Générateur")

        layout.addWidget(self._tabs)
        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def get_updated_config(self) -> dict:
        """Retourne la config avec serial_multimeter et serial_generator mis à jour."""
        out = dict(self._config)
        out["serial_multimeter"] = self._form_multimeter.get_values()
        out["serial_generator"] = self._form_generator.get_values()
        return out
