"""
Barre de statut de connexion — 4 équipements (Phase 3 maquette), version compacte.

Deux lignes : (1) 4 pastilles avec libellés courts, (2) boutons d’action.
Réduit la largeur horizontale tout en restant lisible et fonctionnel.

UI_CHANGES_VIA_MAQUETTE: Cette version est la maquette ; valider puis reporter vers ui/.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
)

from .status_indicator import StatusIndicator


# Ordre et libellés courts pour limiter la largeur
EQUIPMENT_ORDER = [
    ("multimeter", "Multim.", "Multimètre"),
    ("generator", "Gén.", "Générateur"),
    ("power_supply", "Alim.", "Alimentation"),
    ("oscilloscope", "Oscillo.", "Oscilloscope"),
]


class ConnectionStatusBar(QWidget):
    """Barre compacte : ligne 1 = 4 pastilles (libellés courts), ligne 2 = boutons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = {key: False for key, _, _ in EQUIPMENT_ORDER}
        self._labels = {}
        self._indicators = {}
        self._tooltip_text = {}  # texte complet pour tooltip
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 4)
        main_layout.setSpacing(4)

        # Ligne 1 : 4 pastilles centrées
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addStretch()
        for i, (key, short_name, full_name) in enumerate(EQUIPMENT_ORDER):
            if i > 0:
                sep = QLabel("|")
                sep.setStyleSheet("color: #666; font-size: 11px;")
                row1.addWidget(sep)
            ind = StatusIndicator(False)
            self._indicators[key] = ind
            row1.addWidget(ind)
            lbl = QLabel(f"{short_name}: —")
            lbl.setStyleSheet("font-size: 12px;")
            self._labels[key] = lbl
            self._tooltip_text[key] = f"{full_name}: Non connecté"
            row1.addWidget(lbl)
        row1.addStretch()
        main_layout.addLayout(row1)

        # Ligne 2 : boutons centrés
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addStretch()
        self._connect_all_btn = QPushButton("Connecter tout")
        self._connect_all_btn.setObjectName("connectAllButton")
        self._connect_all_btn.setToolTip("Connecter les 4 équipements selon la config (équivalent Charger config).")
        row2.addWidget(self._connect_all_btn)

        self._disconnect_all_btn = QPushButton("Déconnecter tout")
        self._disconnect_all_btn.setObjectName("disconnectAllButton")
        self._disconnect_all_btn.setToolTip("Déconnecter tous les équipements.")
        row2.addWidget(self._disconnect_all_btn)

        row2.addSpacing(12)

        self._load_config_btn = QPushButton("Charger config")
        self._load_config_btn.setObjectName("loadConfigButton")
        self._load_config_btn.setToolTip("Récupère la config depuis config.json et tente de se connecter.")
        row2.addWidget(self._load_config_btn)

        self._detect_btn = QPushButton("Détecter")
        self._detect_btn.setObjectName("detectButton")
        row2.addWidget(self._detect_btn)

        self._params_btn = QPushButton("Paramètres")
        self._params_btn.setObjectName("paramsButton")
        self._params_btn.setToolTip("Configuration série (ports, débits). Sauvegarder avec Fichier → Sauvegarder config.")
        row2.addWidget(self._params_btn)

        row2.addStretch()
        main_layout.addLayout(row2)

        self._progress = QProgressBar()
        self._progress.setMaximumHeight(4)
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        main_layout.addWidget(self._progress)

    def _update_label(self, key: str, short_name: str, full_name: str, connected: bool, detail: str):
        self._labels[key].setText(f"{short_name}: {detail}")
        self._tooltip_text[key] = f"{full_name}: {'Connecté — ' + detail if connected else 'Non connecté'}"
        self._labels[key].setToolTip(self._tooltip_text[key])

    def show_detection_progress(self) -> None:
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._detect_btn.setEnabled(False)

    def hide_detection_progress(self) -> None:
        self._progress.setVisible(False)
        self._progress.setRange(0, 100)
        self._detect_btn.setEnabled(True)

    def set_multimeter_status(self, connected: bool, model: str = "", port: str = ""):
        self._status["multimeter"] = connected
        self._indicators["multimeter"].set_connected(connected)
        short_name = next(s for k, s, _ in EQUIPMENT_ORDER if k == "multimeter")
        full_name = next(f for k, _, f in EQUIPMENT_ORDER if k == "multimeter")
        detail = f"{port}" if connected and port else "—"
        self._update_label("multimeter", short_name, full_name, connected, detail)

    def set_generator_status(self, connected: bool, model: str = "", port: str = ""):
        self._status["generator"] = connected
        self._indicators["generator"].set_connected(connected)
        short_name = next(s for k, s, _ in EQUIPMENT_ORDER if k == "generator")
        full_name = next(f for k, _, f in EQUIPMENT_ORDER if k == "generator")
        detail = f"{port}" if connected and port else "—"
        self._update_label("generator", short_name, full_name, connected, detail)

    def set_power_supply_status(self, connected: bool, model: str = "", port: str = ""):
        self._status["power_supply"] = connected
        self._indicators["power_supply"].set_connected(connected)
        short_name = next(s for k, s, _ in EQUIPMENT_ORDER if k == "power_supply")
        full_name = next(f for k, _, f in EQUIPMENT_ORDER if k == "power_supply")
        detail = f"{port}" if connected and port else "—"
        self._update_label("power_supply", short_name, full_name, connected, detail)

    def set_oscilloscope_status(self, connected: bool, model: str = "", label: str = ""):
        self._status["oscilloscope"] = connected
        self._indicators["oscilloscope"].set_connected(connected)
        short_name = next(s for k, s, _ in EQUIPMENT_ORDER if k == "oscilloscope")
        full_name = next(f for k, _, f in EQUIPMENT_ORDER if k == "oscilloscope")
        detail = label or "USB" if connected else "—"
        self._update_label("oscilloscope", short_name, full_name, connected, detail)

    def get_load_config_button(self):
        return self._load_config_btn

    def get_params_button(self):
        return self._params_btn

    def get_detect_button(self):
        return self._detect_btn

    def get_connect_all_button(self):
        return self._connect_all_btn

    def get_disconnect_all_button(self):
        return self._disconnect_all_btn
