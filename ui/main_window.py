"""
Fenêtre principale : menu, barre de connexion, onglets.
Connectée au config et au core (connexions série, FilterTest).
"""
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtGui import QAction

from ui.widgets import ConnectionStatusBar
from ui.views import MeterView, GeneratorView, LoggingView, FilterTestView
from ui.dialogs import DeviceDetectionDialog, SerialConfigDialog

# Import core et config (optionnel si non disponibles)
try:
    from config.settings import load_config, save_config, get_serial_multimeter_config, get_serial_generator_config, get_filter_test_config, get_generator_config, DEFAULT_CONFIG_PATH
except ImportError:
    load_config = save_config = None
    get_serial_multimeter_config = get_serial_generator_config = get_filter_test_config = get_generator_config = None
    DEFAULT_CONFIG_PATH = Path("config/config.json")

try:
    from serial import SerialException
    from core.serial_connection import SerialConnection
    from core.scpi_protocol import ScpiProtocol
    from core.measurement import Measurement
    from core.fy6900_protocol import Fy6900Protocol
    from core.filter_test import FilterTest, FilterTestConfig
except ImportError:
    SerialException = Exception
    SerialConnection = ScpiProtocol = Measurement = Fy6900Protocol = FilterTest = FilterTestConfig = None


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Banc de test automatique")
        self._config = {}
        self._multimeter_conn = None
        self._generator_conn = None
        self._scpi = None
        self._measurement = None
        self._fy6900 = None
        self._filter_test = None

        if load_config:
            self._config = load_config()
        self._build_menu()
        self._build_central()
        self._connect_connection_bar()
        self._setup_core()
        self._update_connection_status()

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
        self._filter_test_view = FilterTestView()
        self._tabs.addTab(self._filter_test_view, "Banc filtre")
        layout.addWidget(self._tabs)

        self.setCentralWidget(central)

    def _build_statusbar(self):
        pass  # optionnel

    def _connect_connection_bar(self):
        self._connection_bar.get_params_button().clicked.connect(self._on_params)

    def _setup_core(self):
        """Crée les connexions série et le banc filtre à partir de la config."""
        if not all([SerialConnection, ScpiProtocol, Measurement, Fy6900Protocol, FilterTest, FilterTestConfig]):
            return
        sm = get_serial_multimeter_config(self._config) if get_serial_multimeter_config else {}
        sg = get_serial_generator_config(self._config) if get_serial_generator_config else {}
        ft_cfg = get_filter_test_config(self._config) if get_filter_test_config else {}

        self._multimeter_conn = SerialConnection(**sm)
        self._generator_conn = SerialConnection(**sg)
        self._scpi = ScpiProtocol(self._multimeter_conn)
        self._measurement = Measurement(self._scpi)
        self._fy6900 = Fy6900Protocol(self._generator_conn)
        self._filter_test = FilterTest(
            self._fy6900,
            self._measurement,
            FilterTestConfig(
                generator_channel=ft_cfg.get("generator_channel", 1),
                f_min_hz=ft_cfg.get("f_min_hz", 10),
                f_max_hz=ft_cfg.get("f_max_hz", 100000),
                n_points=ft_cfg.get("n_points", 50),
                scale=ft_cfg.get("scale", "log"),
                settling_ms=ft_cfg.get("settling_ms", 200),
                ue_rms=ft_cfg.get("ue_rms", 1.0),
            ),
        )
        self._filter_test_view.set_filter_test(self._filter_test)
        self._filter_test_view.load_config(self._config)

        # Tenter d'ouvrir les ports au démarrage
        try:
            self._multimeter_conn.open()
        except Exception:
            pass
        try:
            self._generator_conn.open()
        except Exception:
            pass

    def _update_connection_status(self):
        """Met à jour les pastilles selon l'état des ports (sans ouvrir si pas encore connecté)."""
        if self._multimeter_conn and self._multimeter_conn.is_open():
            port = get_serial_multimeter_config(self._config).get("port", "?") if get_serial_multimeter_config else "?"
            self._connection_bar.set_multimeter_status(True, "XDM", port)
        else:
            self._connection_bar.set_multimeter_status(False)

        if self._generator_conn and self._generator_conn.is_open():
            port = get_serial_generator_config(self._config).get("port", "?") if get_serial_generator_config else "?"
            self._connection_bar.set_generator_status(True, "FY6900", port)
        else:
            self._connection_bar.set_generator_status(False)

    def _on_detect_devices(self):
        dlg = DeviceDetectionDialog(self)
        dlg.exec()

    def _on_params(self):
        dlg = SerialConfigDialog("Paramètres série", self)
        dlg.exec()

    def _on_open_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir la configuration", "", "JSON (*.json)")
        if path and load_config:
            self._config = load_config(path)
            self._filter_test_view.load_config(self._config)
            self.statusBar().showMessage(f"Config chargée : {path}") if hasattr(self, "statusBar") and self.statusBar() else None

    def _on_save_config(self):
        if save_config and self._config:
            save_config(self._config)
            self.statusBar().showMessage("Config enregistrée.") if hasattr(self, "statusBar") and self.statusBar() else None

    def _on_save_config_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la configuration sous", "", "JSON (*.json)")
        if path and save_config and self._config:
            save_config(self._config, path)
            self.statusBar().showMessage(f"Config enregistrée : {path}") if hasattr(self, "statusBar") and self.statusBar() else None
