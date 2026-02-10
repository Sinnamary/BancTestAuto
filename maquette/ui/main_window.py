"""
Fenêtre principale de la maquette : menu, barre de connexion, onglets, barre de statut.
Aucune dépendance vers core/ ou config/.
"""
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMenuBar,
    QStatusBar,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtGui import QAction

from ui.widgets import ConnectionStatusBar
from ui.views import (
    MeterView,
    GeneratorView,
    LoggingView,
    FilterTestView,
    FilterCalculatorView,
    PowerSupplyView,
    SerialTerminalView,
    OscilloscopeView,
)
from ui.dialogs import DeviceDetectionDialog


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Banc de test automatique — Maquette")
        self._build_menu()
        self._build_central()
        self._build_statusbar()
        self._connect_connection_bar()

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Fichier")
        file_menu.addAction("Ouvrir config...", self._on_open_config)
        file_menu.addAction("Sauvegarder config", self._on_save_config)
        file_menu.addAction("Enregistrer config sous...", self._on_save_config_as)
        file_menu.addSeparator()
        file_menu.addAction("Quitter", self.close)
        tools_menu = menubar.addMenu("Outils")
        tools_menu.addAction("Détecter les équipements...", self._on_detect_devices)
        menubar.addMenu("?")

    def _build_central(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._connection_bar = ConnectionStatusBar(self)
        layout.addWidget(self._connection_bar)

        self._tabs = QTabWidget()
        self._tabs.addTab(MeterView(), "Multimètre")
        self._tabs.addTab(GeneratorView(), "Générateur")
        self._tabs.addTab(LoggingView(), "Enregistrement")
        self._tabs.addTab(FilterTestView(), "Banc filtre")
        self._tabs.addTab(FilterCalculatorView(), "Calcul filtre")
        self._tabs.addTab(PowerSupplyView(), "Alimentation")
        self._tabs.addTab(SerialTerminalView(), "Terminal série")
        self._tabs.addTab(OscilloscopeView(), "Oscilloscope")
        layout.addWidget(self._tabs)

        self.setCentralWidget(central)

    def _build_statusbar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Maquette — aucune connexion réelle")

    def _connect_connection_bar(self):
        self._connection_bar.get_params_button().clicked.connect(self._on_params)

    def _on_detect_devices(self):
        dlg = DeviceDetectionDialog(self)
        dlg.exec()

    def _on_params(self):
        # Placeholder : après intégration, ouvrir SerialConfigDialog
        QMessageBox.information(
            self,
            "Paramètres",
            "Dialogue de configuration série (multimètre / générateur) — à brancher à l'intégration.",
        )

    def _on_open_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir la configuration", "", "JSON (*.json)")
        if path:
            self._status.showMessage(f"Ouvert : {path} (maquette : non chargé)")

    def _on_save_config(self):
        self._status.showMessage("Sauvegarde config (maquette : non enregistré)")

    def _on_save_config_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la configuration sous", "", "JSON (*.json)")
        if path:
            self._status.showMessage(f"Enregistrer sous : {path} (maquette : non enregistré)")
