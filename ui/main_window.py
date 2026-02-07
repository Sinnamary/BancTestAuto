"""
Fenêtre principale : menu, barre de connexion, onglets.
Connectée au config et au core (connexions série, FilterTest).
"""
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QDialog,
)
from PyQt6.QtGui import QAction, QActionGroup

from ui.widgets import ConnectionStatusBar
from ui.views import MeterView, GeneratorView, LoggingView, FilterTestView
from ui.dialogs import DeviceDetectionDialog, SerialConfigDialog, ViewConfigDialog

# Import core et config (optionnel si non disponibles)
try:
    from config.settings import load_config, save_config, get_serial_multimeter_config, get_serial_generator_config, get_filter_test_config, get_generator_config, DEFAULT_CONFIG_PATH
except ImportError:
    load_config = save_config = None
    get_serial_multimeter_config = get_serial_generator_config = get_filter_test_config = get_generator_config = None
    DEFAULT_CONFIG_PATH = Path("config/config.json")

try:
    from serial import SerialException
    from core.device_detection import detect_devices, update_config_ports
    from core.serial_connection import SerialConnection
    from core.scpi_protocol import ScpiProtocol
    from core.measurement import Measurement
    from core.fy6900_protocol import Fy6900Protocol
    from core.filter_test import FilterTest, FilterTestConfig
    from core.data_logger import DataLogger
except ImportError:
    SerialException = Exception
    detect_devices = update_config_ports = None
    SerialConnection = ScpiProtocol = Measurement = Fy6900Protocol = FilterTest = FilterTestConfig = None
    DataLogger = None

try:
    from core.serial_exchange_logger import SerialExchangeLogger
except ImportError:
    SerialExchangeLogger = None

try:
    from core.app_logger import get_logger, set_level as set_log_level, get_current_level_name
except ImportError:
    def get_logger(_name):
        import logging
        return logging.getLogger(_name)
    def set_log_level(_x):
        pass
    def get_current_level_name():
        return "INFO"

logger = get_logger(__name__)


class DetectionWorker(QThread):
    """Thread pour la détection des équipements (évite de bloquer l'UI)."""
    result = pyqtSignal(object, object)

    def run(self):
        if detect_devices is None:
            self.result.emit(None, None)
            return
        m, g = detect_devices()
        self.result.emit(m, g)


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
        self._data_logger = None
        self._serial_exchange_logger = None
        self._detection_worker = None

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
        file_menu.addAction("Voir config JSON (lecture seule)", self._on_view_config)
        file_menu.addSeparator()
        file_menu.addAction("Quitter", self.close)
        tools_menu = menubar.addMenu("Outils")
        tools_menu.addAction("Détecter les équipements...", self._on_detect_devices)

        config_menu = menubar.addMenu("Configuration")
        log_level_menu = config_menu.addMenu("Niveau de log")
        self._log_level_group = QActionGroup(self)
        self._log_level_group.setExclusive(True)
        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            action = QAction(level, self, checkable=True)
            action.triggered.connect(lambda checked, l=level: self._on_log_level(l))
            self._log_level_group.addAction(action)
            log_level_menu.addAction(action)
        self._log_level_actions = {a.text(): a for a in self._log_level_group.actions()}
        self._update_log_level_menu()

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
        self._connection_bar.get_detect_button().clicked.connect(self._on_detect_clicked)

    def _setup_core(self):
        """Crée les connexions série et le banc filtre à partir de la config."""
        if not all([SerialConnection, ScpiProtocol, Measurement, Fy6900Protocol, FilterTest, FilterTestConfig]):
            return
        sm = get_serial_multimeter_config(self._config) if get_serial_multimeter_config else {}
        sg = get_serial_generator_config(self._config) if get_serial_generator_config else {}
        ft_cfg = get_filter_test_config(self._config) if get_filter_test_config else {}

        if SerialExchangeLogger and self._serial_exchange_logger is None:
            log_dir = self._config.get("logging", {}).get("output_dir", "./logs")
            self._serial_exchange_logger = SerialExchangeLogger(log_dir=log_dir)
        if self._serial_exchange_logger:
            sm = dict(sm)
            sg = dict(sg)
            sm["log_exchanges"] = True
            sg["log_exchanges"] = True
            sm["log_callback"] = self._serial_exchange_logger.get_callback("multimeter")
            sg["log_callback"] = self._serial_exchange_logger.get_callback("generator")

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

        if DataLogger:
            self._data_logger = DataLogger()
            self._data_logger.set_measurement(self._measurement)

        # Pas d'ouverture des ports au démarrage : l'utilisateur lance la détection via le bouton « Détecter »
        self._inject_views()

    def _inject_views(self):
        """Passe les références core aux vues (multimètre, générateur, enregistrement)."""
        meter = self._tabs.widget(0)
        if hasattr(meter, "set_measurement") and self._measurement:
            meter.set_measurement(self._measurement)
        gen = self._tabs.widget(1)
        if hasattr(gen, "set_fy6900") and self._fy6900:
            gen.set_fy6900(self._fy6900)
        logging_view = self._tabs.widget(2)
        if hasattr(logging_view, "set_data_logger") and self._data_logger:
            logging_view.set_data_logger(self._data_logger)
        if hasattr(logging_view, "load_config") and self._config:
            logging_view.load_config(self._config)

    def _reconnect_serial(self):
        """Ferme les ports, recrée les connexions, ouvre et vérifie les appareils."""
        if self._multimeter_conn:
            self._multimeter_conn.close()
        if self._generator_conn:
            self._generator_conn.close()
        self._setup_core()
        self._inject_views()
        self._open_and_verify_connections()
        self._update_connection_status()

    def _open_and_verify_connections(self):
        """Ouvre les ports puis vérifie que les appareils répondent (IDN? / FY6900)."""
        try:
            if self._multimeter_conn:
                self._multimeter_conn.open()
        except Exception:
            pass
        try:
            if self._generator_conn:
                self._generator_conn.open()
        except Exception:
            pass
        self._verify_connections()

    def _verify_connections(self):
        """
        Vérifie que les appareils répondent vraiment (pas seulement que le port est ouvert).
        Sous Windows, open() peut réussir même sans appareil branché.
        """
        if not self._multimeter_conn or not self._scpi:
            return
        # Multimètre : port ouvert ET réponse à *IDN? avec OWON/XDM
        multimeter_ok = False
        if self._multimeter_conn.is_open():
            try:
                r = self._scpi.idn()
                multimeter_ok = r and ("OWON" in r.upper() or "XDM" in r.upper())
            except Exception:
                pass
        if not multimeter_ok and self._multimeter_conn.is_open():
            self._multimeter_conn.close()

        if not self._generator_conn or not self._fy6900:
            return
        # Générateur : port ouvert ET pas d'erreur sur une commande (WMN0)
        generator_ok = False
        if self._generator_conn.is_open():
            try:
                self._fy6900.set_output(False)
                generator_ok = True
            except Exception:
                pass
        if not generator_ok and self._generator_conn.is_open():
            self._generator_conn.close()

    def _update_connection_status(self):
        """Met à jour les pastilles selon l'état vérifié des connexions."""
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

    def _on_detect_clicked(self):
        """Bouton Détecter : lance la détection en thread avec barre de progression."""
        logger.debug("Clic Détecter — lancement du worker")
        if not detect_devices or not update_config_ports:
            QMessageBox.warning(self, "Détection", "Module de détection non disponible.")
            return
        self._connection_bar.show_detection_progress()
        self._detection_worker = DetectionWorker()
        self._detection_worker.result.connect(self._on_detection_result)
        self._detection_worker.finished.connect(self._on_detection_finished)
        self._detection_worker.start()

    def _on_detection_result(self, multimeter_port, generator_port):
        logger.info("Détection: multimètre=%s, générateur=%s", multimeter_port, generator_port)
        self._config = update_config_ports(self._config, multimeter_port, generator_port)
        self._reconnect_serial()
        if self.statusBar():
            msg = []
            if multimeter_port:
                msg.append(f"Multimètre : {multimeter_port}")
            else:
                msg.append("Multimètre : non trouvé")
            if generator_port:
                msg.append(f"Générateur : {generator_port}")
            else:
                msg.append("Générateur : non trouvé")
            self.statusBar().showMessage(" — ".join(msg))

    def _on_detection_finished(self):
        self._connection_bar.hide_detection_progress()
        self._detection_worker = None

    def _update_log_level_menu(self) -> None:
        """Coche l’action correspondant au niveau de log actuel (config ou logger)."""
        current = (self._config.get("logging") or {}).get("level", "INFO")
        current = str(current).upper()
        if current not in self._log_level_actions:
            current = "INFO"
        for name, action in self._log_level_actions.items():
            action.setChecked(name == current)

    def _on_log_level(self, level: str) -> None:
        """Change le niveau de log (menu Configuration > Niveau de log)."""
        if "logging" not in self._config:
            self._config["logging"] = {}
        self._config["logging"]["level"] = level
        set_log_level(level)
        self._update_log_level_menu()
        if self.statusBar():
            self.statusBar().showMessage(f"Niveau de log : {level}. Enregistrez la config pour conserver.")
        logger.info("Niveau de log défini à %s", level)

    def _on_detect_devices(self):
        dlg = DeviceDetectionDialog(
            self,
            config=self._config,
            on_config_updated=self._on_detection_config_updated,
        )
        dlg.exec()

    def _on_detection_config_updated(self, new_config: dict):
        """Après détection : applique la nouvelle config (ports) et reconnecte."""
        self._config = new_config
        self._reconnect_serial()
        self._update_connection_status()
        if self._filter_test_view and get_filter_test_config:
            self._filter_test_view.load_config(self._config)

    def _on_params(self):
        dlg = SerialConfigDialog(config=self._config, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._config = dlg.get_updated_config()
            self._reconnect_serial()
            if self.statusBar():
                self.statusBar().showMessage("Configuration série mise à jour. Enregistrez la config pour conserver.")

    def _on_open_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir la configuration", "", "JSON (*.json)")
        if path and load_config:
            self._config = load_config(path)
            self._filter_test_view.load_config(self._config)
            logging_view = self._tabs.widget(2)
            if hasattr(logging_view, "load_config"):
                logging_view.load_config(self._config)
            if self.statusBar():
                self.statusBar().showMessage(f"Config chargée : {path}")

    def _on_save_config(self):
        if save_config and self._config:
            save_config(self._config)
            self.statusBar().showMessage("Config enregistrée.") if hasattr(self, "statusBar") and self.statusBar() else None

    def _on_save_config_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la configuration sous", "", "JSON (*.json)")
        if path and save_config and self._config:
            save_config(self._config, path)
            self.statusBar().showMessage(f"Config enregistrée : {path}") if hasattr(self, "statusBar") and self.statusBar() else None

    def _on_view_config(self):
        """Ouvre une fenêtre en lecture seule sur le contenu JSON (config en mémoire)."""
        dlg = ViewConfigDialog(
            config_path=DEFAULT_CONFIG_PATH if load_config else None,
            config_dict=self._config,
            parent=self,
        )
        dlg.exec()
