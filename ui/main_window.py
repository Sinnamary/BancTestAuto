"""
Fenêtre principale : menu, barre de connexion, onglets.
Connectée au config et au core (connexions série, FilterTest).

UI_CHANGES_VIA_MAQUETTE: Les évolutions d'interface (barre 4 équipements, connexion globale,
menus, onglets) se font dans la maquette ; valider puis reporter vers ui/. Voir docs/EVOLUTION_4_EQUIPEMENTS.md.

OBSOLETE_AFTER_MIGRATION: La logique connexion 2 équipements (bridge, _reconnect_serial,
_update_connection_status) sera remplacée par ConnectionController, BenchConnectionState (Phase 3).
Le bouton Détecter ouvre désormais le dialogue 4 équipements (DeviceDetectionDialog4).
"""
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QFrame,
    QMessageBox,
    QFileDialog,
    QApplication,
)
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut

from ui.widgets import ConnectionStatusBar
from ui.views import MeterView, GeneratorView, LoggingView, FilterTestView, FilterCalculatorView, PowerSupplyView, SerialTerminalView, OscilloscopeView
from ui.dialogs import (
    DeviceDetectionDialog,
    DeviceDetectionDialog4,
    ViewConfigDialog,
    ViewLogDialog,
    HelpDialog,
    AboutDialog,
)
from ui.bode_csv_viewer import open_viewer as open_bode_csv_viewer
from ui.theme_loader import get_theme_stylesheet
from ui.connection_bridge import MainWindowConnectionBridge

# Import core et config (optionnel si non disponibles)
try:
    from config.settings import (
        load_config,
        save_config,
        get_serial_multimeter_config,
        get_serial_generator_config,
        get_filter_test_config,
        get_generator_config,
        get_config_file_path,
        DEFAULT_CONFIG_PATH,
    )
except ImportError:
    load_config = save_config = None
    get_serial_multimeter_config = get_serial_generator_config = get_filter_test_config = get_generator_config = None
    get_config_file_path = lambda: Path("config/config.json")
    DEFAULT_CONFIG_PATH = Path("config/config.json")

try:
    from serial import SerialException
    from core.device_detection import detect_devices, update_config_ports
    from core.serial_connection import SerialConnection
    from core.scpi_protocol import ScpiProtocol
    from core.measurement import Measurement
    from core.fy6900_protocol import Fy6900Protocol
    from core.filter_test import FilterTest, FilterTestConfig, BodePoint
    from core.data_logger import DataLogger
except ImportError:
    SerialException = Exception
    detect_devices = update_config_ports = None
    SerialConnection = ScpiProtocol = Measurement = Fy6900Protocol = FilterTest = FilterTestConfig = BodePoint = None
    DataLogger = None

try:
    from core.serial_exchange_logger import SerialExchangeLogger
except ImportError:
    SerialExchangeLogger = None

try:
    from core.app_logger import get_logger, set_level as set_log_level, get_current_level_name, get_latest_log_path
except ImportError:
    def get_logger(_name):
        import logging
        return logging.getLogger(_name)
    def set_log_level(_x):
        pass
    def get_current_level_name():
        return "INFO"
    get_latest_log_path = None

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Banc de test automatique")
        self._config = {}
        self._connection_bridge = MainWindowConnectionBridge()
        self._detection_worker = None

        if load_config:
            self._config = load_config()
        self._build_menu()
        self._build_central()
        self._connect_connection_bar()
        self._setup_shortcuts()
        # Pas d'ouverture de ports au démarrage : utiliser "Connecter tout" ou "Détecter" pour connecter
        self._init_views_without_connections()
        self._update_connection_status()

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Fichier")
        file_menu.addAction("Ouvrir config...", self._on_open_config)
        file_menu.addAction("Ouvrir CSV Banc filtre...", self._on_open_bode_csv)
        file_menu.addAction("Sauvegarder config", self._on_save_config)
        file_menu.addAction("Enregistrer config sous...", self._on_save_config_as)
        file_menu.addSeparator()
        file_menu.addAction("Voir config JSON (lecture seule)", self._on_view_config)
        file_menu.addAction("Lire le dernier log", self._on_view_latest_log)
        file_menu.addSeparator()
        file_menu.addAction("Quitter", self.close)
        tools_menu = menubar.addMenu("Outils")
        tools_menu.addAction("Détecter les équipements...", self._on_detect_devices)

        config_menu = menubar.addMenu("Configuration")
        # Sous-menu Thème (clair / foncé)
        theme_menu = config_menu.addMenu("Thème")
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_actions = {}
        for label, theme_id in (("Clair", "light"), ("Foncé", "dark")):
            action = QAction(label, self, checkable=True)
            action.triggered.connect(lambda checked, t=theme_id: self._on_theme(t))
            self._theme_group.addAction(action)
            theme_menu.addAction(action)
            self._theme_actions[theme_id] = action
        self._update_theme_menu()
        config_menu.addSeparator()
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

        help_menu = menubar.addMenu("Aide")
        help_menu.addAction("Manuel", QKeySequence("F1"), self._on_help)
        help_menu.addSeparator()
        help_menu.addAction("A propos...", self._on_about)
        sub_owon = help_menu.addMenu("Multimètre OWON")
        sub_owon.addAction("Commandes (documentation)", lambda: self._on_help_doc("COMMANDES_OWON.md"))
        sub_fy6900 = help_menu.addMenu("Générateur FY6900")
        sub_fy6900.addAction("Commandes (documentation)", lambda: self._on_help_doc("COMMANDES_FY6900.md"))
        sub_rs305p = help_menu.addMenu("Alimentation RS305P")
        sub_rs305p.addAction("Commandes (documentation)", lambda: self._on_help_doc("COMMANDES_RS305P.md"))
        sub_dos1102 = help_menu.addMenu("Oscilloscope DOS1102")
        sub_dos1102.addAction("Commandes (documentation)", lambda: self._on_help_doc("COMMANDES_HANMATEK_DOS1102.md"))

    def _build_central(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._connection_bar = ConnectionStatusBar(self)
        layout.addWidget(self._connection_bar)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #555; max-height: 1px; margin: 2px 8px;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        self._tabs = QTabWidget()
        self._tabs.addTab(MeterView(), "Multimètre")
        self._tabs.addTab(GeneratorView(), "Générateur")
        self._tabs.addTab(LoggingView(), "Enregistrement")
        self._filter_test_view = FilterTestView()
        self._tabs.addTab(self._filter_test_view, "Banc filtre")
        self._tabs.addTab(FilterCalculatorView(), "Calcul filtre")
        self._power_supply_view = PowerSupplyView()
        self._tabs.addTab(self._power_supply_view, "Alimentation")
        self._serial_terminal_view = SerialTerminalView()
        self._tabs.addTab(self._serial_terminal_view, "Terminal série")
        self._oscilloscope_view = OscilloscopeView()
        self._tabs.addTab(self._oscilloscope_view, "Oscilloscope")
        layout.addWidget(self._tabs)

        self.setCentralWidget(central)

    def _build_statusbar(self):
        pass  # optionnel

    def _connect_connection_bar(self):
        self._connection_bar.get_detect_button().clicked.connect(self._on_detect_clicked)
        if hasattr(self._connection_bar, "get_connect_all_button"):
            self._connection_bar.get_connect_all_button().clicked.connect(self._on_connect_all)
        if hasattr(self._connection_bar, "get_disconnect_all_button"):
            self._connection_bar.get_disconnect_all_button().clicked.connect(self._on_disconnect_all)

    def _setup_shortcuts(self):
        """Raccourcis clavier : F5 mesure, Ctrl+M mesure continue, Ctrl+R reset, Ctrl+E export CSV."""
        self._shortcut_measure = QShortcut(QKeySequence("F5"), self)
        self._shortcut_measure.activated.connect(self._on_shortcut_measure)
        self._shortcut_continuous = QShortcut(QKeySequence("Ctrl+M"), self)
        self._shortcut_continuous.activated.connect(self._on_shortcut_continuous)
        self._shortcut_reset = QShortcut(QKeySequence("Ctrl+R"), self)
        self._shortcut_reset.activated.connect(self._on_shortcut_reset)
        self._shortcut_export = QShortcut(QKeySequence("Ctrl+E"), self)
        self._shortcut_export.activated.connect(self._on_shortcut_export)

    def _meter_view(self):
        """Onglet Multimètre (index 0) ou None."""
        if self._tabs.count() > 0:
            return self._tabs.widget(0)
        return None

    def _on_shortcut_measure(self):
        meter = self._meter_view()
        if meter is not None and hasattr(meter, "trigger_measure"):
            meter.trigger_measure()

    def _on_shortcut_continuous(self):
        meter = self._meter_view()
        if meter is not None and hasattr(meter, "toggle_continuous_measure"):
            meter.toggle_continuous_measure()

    def _on_shortcut_reset(self):
        meter = self._meter_view()
        if meter is not None and hasattr(meter, "trigger_reset"):
            meter.trigger_reset()

    def _on_shortcut_export(self):
        meter = self._meter_view()
        if meter is not None and hasattr(meter, "trigger_export_csv"):
            meter.trigger_export_csv()

    def _setup_core(self):
        """Crée les connexions série et le banc filtre via le pont de connexion (bridge)."""
        self._connection_bridge.reconnect(self._config)
        if self._connection_bridge.get_filter_test():
            self._filter_test_view.set_filter_test(self._connection_bridge.get_filter_test())
        self._filter_test_view.load_config(self._config)

    def _inject_views(self):
        """Passe les références core aux vues (multimètre, générateur, enregistrement, etc.)."""
        bridge = self._connection_bridge
        measurement = bridge.get_measurement()
        fy6900 = bridge.get_fy6900()
        data_logger = bridge.get_data_logger()
        meter = self._tabs.widget(0)
        if hasattr(meter, "set_measurement") and measurement:
            meter.set_measurement(measurement)
        if hasattr(meter, "load_config") and self._config:
            meter.load_config(self._config)
        gen = self._tabs.widget(1)
        if hasattr(gen, "set_fy6900") and fy6900:
            gen.set_fy6900(fy6900)
        logging_view = self._tabs.widget(2)
        if hasattr(logging_view, "set_data_logger") and data_logger:
            logging_view.set_data_logger(data_logger)
        if hasattr(logging_view, "load_config") and self._config:
            logging_view.load_config(self._config)
        if hasattr(self, "_power_supply_view") and self._power_supply_view:
            if hasattr(self._power_supply_view, "load_config") and self._config:
                self._power_supply_view.load_config(self._config)
            if hasattr(self._power_supply_view, "set_connection"):
                self._power_supply_view.set_connection(bridge.get_power_supply_conn())
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "load_config") and self._config:
            self._serial_terminal_view.load_config(self._config)
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "set_connection_provider"):
            self._serial_terminal_view.set_connection_provider(
                lambda: self._connection_bridge.get_connected_equipment_for_terminal()
            )
        if hasattr(self, "_oscilloscope_view") and self._oscilloscope_view and hasattr(self._oscilloscope_view, "load_config") and self._config:
            self._oscilloscope_view.load_config(self._config)

    def _init_views_without_connections(self):
        """Initialise les vues sans créer ni ouvrir de connexion série (aucun port ouvert au démarrage)."""
        if self._config and self._filter_test_view:
            self._filter_test_view.load_config(self._config)
            self._filter_test_view.set_filter_test(None)
        logging_view = self._tabs.widget(2) if self._tabs.count() > 2 else None
        if logging_view and hasattr(logging_view, "load_config") and self._config:
            logging_view.load_config(self._config)
        if hasattr(self, "_power_supply_view") and self._power_supply_view:
            if hasattr(self._power_supply_view, "load_config") and self._config:
                self._power_supply_view.load_config(self._config)
            if hasattr(self._power_supply_view, "set_connection"):
                self._power_supply_view.set_connection(None)
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "load_config") and self._config:
            self._serial_terminal_view.load_config(self._config)
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "set_connection_provider"):
            self._serial_terminal_view.set_connection_provider(
                lambda: self._connection_bridge.get_connected_equipment_for_terminal()
            )
        if hasattr(self, "_oscilloscope_view") and self._oscilloscope_view and hasattr(self._oscilloscope_view, "load_config") and self._config:
            self._oscilloscope_view.load_config(self._config)

    def _reconnect_serial(self):
        """Ferme les ports, recrée les connexions, ouvre et vérifie les appareils (Connecter tout / Détecter)."""
        self._setup_core()
        self._inject_views()
        self._update_connection_status()

    def _update_connection_status(self):
        """Met à jour les 4 pastilles (bridge = multimètre + générateur ; alimentation et oscillo non gérés par le bridge pour l'instant)."""
        state = self._connection_bridge.get_state()
        if state.multimeter_connected:
            self._connection_bar.set_multimeter_status(True, state.multimeter_name, state.multimeter_port)
        else:
            self._connection_bar.set_multimeter_status(False)
        if state.generator_connected:
            self._connection_bar.set_generator_status(True, state.generator_name, state.generator_port)
        else:
            self._connection_bar.set_generator_status(False)
        if hasattr(self._connection_bar, "set_power_supply_status"):
            self._connection_bar.set_power_supply_status(
                state.power_supply_connected,
                "",
                state.power_supply_port or "—",
            )
        if hasattr(self._connection_bar, "set_oscilloscope_status"):
            self._connection_bar.set_oscilloscope_status(
                state.oscilloscope_connected,
                "",
                state.oscilloscope_label or "—",
            )
        if hasattr(self, "_power_supply_view") and self._power_supply_view and hasattr(self._power_supply_view, "set_connection"):
            self._power_supply_view.set_connection(self._connection_bridge.get_power_supply_conn())
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "refresh_equipment_list"):
            self._serial_terminal_view.refresh_equipment_list()

    def _on_connect_all(self):
        """Connexion globale : relit config.json et ouvre les connexions (multimètre, générateur, alimentation, oscilloscope)."""
        self._on_load_config_clicked()

    def _on_disconnect_all(self):
        """Déconnexion globale : ferme toutes les connexions et met à jour les pastilles."""
        self._connection_bridge.close()
        self._update_connection_status()
        if self.statusBar():
            self.statusBar().showMessage("Tous les équipements déconnectés.")

    def _on_load_config_clicked(self):
        """Relit config.json et tente de se connecter à tous les équipements (appelé par Connecter tout)."""
        if not load_config:
            QMessageBox.warning(self, "Config", "Chargement de la config non disponible.")
            return
        try:
            config_path = get_config_file_path() if get_config_file_path else Path("config/config.json")
            if not config_path.exists():
                QMessageBox.warning(
                    self,
                    "Connecter tout",
                    f"Fichier introuvable : {config_path}\n\n"
                    "Vérifiez que config.json existe (ex. config/config.json).",
                )
                return
            self._config = load_config()
            self._reconnect_serial()
            self._update_connection_status()
            if self._filter_test_view and get_filter_test_config:
                self._filter_test_view.load_config(self._config)
            if self._serial_terminal_view and hasattr(self._serial_terminal_view, "load_config"):
                self._serial_terminal_view.load_config(self._config)
            if self._power_supply_view and hasattr(self._power_supply_view, "load_config"):
                self._power_supply_view.load_config(self._config)
            if self._oscilloscope_view and hasattr(self._oscilloscope_view, "load_config"):
                self._oscilloscope_view.load_config(self._config)
            sm = get_serial_multimeter_config(self._config) if get_serial_multimeter_config else {}
            sg = get_serial_generator_config(self._config) if get_serial_generator_config else {}
            msg = f"Config : {config_path.name} — Multimètre {sm.get('port', '?')} @ {sm.get('baudrate', '?')} bauds, Générateur {sg.get('port', '?')} @ {sg.get('baudrate', '?')} bauds."
            if self.statusBar():
                self.statusBar().showMessage(msg)
            logger.info("Config rechargée depuis %s", config_path)
        except Exception as e:
            logger.exception("Connecter tout")
            QMessageBox.warning(
                self,
                "Connecter tout",
                f"Impossible de charger la config : {e}",
            )

    def _on_detect_clicked(self):
        """Bouton Détecter : ouvre le dialogue de détection (4 équipements). Les ports sont libérés avant."""
        self._prepare_and_open_detection_dialog()

    def _prepare_and_open_detection_dialog(self):
        """Ferme les connexions pour libérer les ports, met à jour les pastilles, puis ouvre le dialogue de détection."""
        self._connection_bridge.close()
        self._update_connection_status()
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "refresh_equipment_list"):
            self._serial_terminal_view.refresh_equipment_list()
        if DeviceDetectionDialog4 is not None:
            dlg = DeviceDetectionDialog4(
                self,
                config=self._config,
                on_config_updated=self._on_detection_config_updated,
            )
        else:
            dlg = DeviceDetectionDialog(
                self,
                config=self._config,
                on_config_updated=self._on_detection_config_updated,
            )
        dlg.exec()

    def _update_theme_menu(self) -> None:
        """Coche l’action correspondant au thème actuel (config display.theme)."""
        current = (self._config.get("display") or {}).get("theme", "dark")
        current = str(current).strip().lower()
        if current not in self._theme_actions:
            current = "dark"
        for theme_id, action in self._theme_actions.items():
            action.setChecked(theme_id == current)

    def _on_theme(self, theme_id: str) -> None:
        """Change le thème (Configuration > Thème > Clair / Foncé) et applique le style."""
        if "display" not in self._config:
            self._config["display"] = {}
        self._config["display"]["theme"] = theme_id
        stylesheet = get_theme_stylesheet(theme_id)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet or "")
        self._update_theme_menu()
        if self.statusBar():
            self.statusBar().showMessage(
                f"Thème {'clair' if theme_id == 'light' else 'foncé'}. Enregistrez la config pour conserver."
            )
        logger.info("Thème défini à %s", theme_id)

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
        """Menu Détecter les équipements : même flux que le bouton barre (dialogue 4 équipements, ports libérés)."""
        self._prepare_and_open_detection_dialog()

    def _on_detection_config_updated(self, new_config: dict):
        """Après détection : applique la nouvelle config (ports) et reconnecte si les ports ont changé."""
        sm_old = (self._config.get("serial_multimeter") or {}).get("port"), (self._config.get("serial_multimeter") or {}).get("baudrate")
        sg_old = (self._config.get("serial_generator") or {}).get("port"), (self._config.get("serial_generator") or {}).get("baudrate")
        sm_new = (new_config.get("serial_multimeter") or {}).get("port"), (new_config.get("serial_multimeter") or {}).get("baudrate")
        sg_new = (new_config.get("serial_generator") or {}).get("port"), (new_config.get("serial_generator") or {}).get("baudrate")
        self._config = new_config
        if (sm_old != sm_new) or (sg_old != sg_new):
            self._reconnect_serial()
        self._update_connection_status()
        if self._filter_test_view and get_filter_test_config:
            self._filter_test_view.load_config(self._config)

    def _on_open_bode_csv(self):
        """Ouvre le visualiseur Bode CSV (module indépendant) avec le fichier sélectionné."""
        default_dir = Path("datas/csv") if Path("datas/csv").exists() else Path(".")
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir CSV Banc filtre", str(default_dir),
            "CSV (*.csv);;Tous (*)"
        )
        if path:
            open_bode_csv_viewer(self, path, config=self._config)

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

    def _update_config_from_views(self) -> None:
        """Recopie les ports / paramètres sélectionnés dans les onglets vers self._config avant sauvegarde."""
        if not self._config:
            return
        # Oscilloscope (USB / PyUSB uniquement) : dernier périphérique sélectionné
        if hasattr(self, "_oscilloscope_view") and self._oscilloscope_view and hasattr(
            self._oscilloscope_view, "get_current_usb_device"
        ):
            usb_dev = self._oscilloscope_view.get_current_usb_device()
            if usb_dev:
                vid, pid = usb_dev
                usb_cfg = dict(self._config.get("usb_oscilloscope") or {})
                usb_cfg["vendor_id"] = int(vid)
                usb_cfg["product_id"] = int(pid)
                self._config["usb_oscilloscope"] = usb_cfg
        # Alimentation : port géré par config/détection, pas par l'onglet

    def _on_save_config(self):
        if save_config and self._config:
            self._update_config_from_views()
            save_config(self._config)
            self.statusBar().showMessage("Config enregistrée.") if hasattr(self, "statusBar") and self.statusBar() else None

    def _on_save_config_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la configuration sous", "", "JSON (*.json)")
        if path and save_config and self._config:
            self._update_config_from_views()
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

    def _on_view_latest_log(self):
        """Ouvre une fenêtre affichant le contenu du dernier fichier de log."""
        if get_latest_log_path is None:
            QMessageBox.warning(
                self,
                "Log",
                "Fonction de lecture du log non disponible.",
            )
            return
        log_path = get_latest_log_path(self._config)
        if log_path is None or not log_path.exists():
            log_dir = Path((self._config.get("logging") or {}).get("output_dir", "./logs"))
            QMessageBox.information(
                self,
                "Log",
                f"Aucun fichier de log trouvé dans {log_dir.resolve()}.\n\n"
                "Les logs sont créés au démarrage de l'application (app_AAAA-MM-JJ_HH-MM-SS.log).",
            )
            return
        dlg = ViewLogDialog(log_path, parent=self)
        dlg.exec()

    def _on_help(self):
        """Ouvre la fenêtre d'aide (manuel utilisateur avec recherche)."""
        self._on_help_doc("AIDE.md")

    def _on_about(self):
        """Ouvre le dialogue À propos (version, date, environnement)."""
        dlg = AboutDialog(parent=self)
        dlg.exec()

    def _on_help_doc(self, doc_filename: str):
        """Ouvre le dialogue d'aide avec le fichier de documentation indiqué (ex. COMMANDES_OWON.md)."""
        from core.app_paths import get_base_path
        root = get_base_path()
        help_path = root / "docs" / doc_filename
        dlg = HelpDialog(help_path=help_path, parent=self)
        title = doc_filename.replace(".md", "").replace("_", " ").title()
        dlg.setWindowTitle(title)
        dlg.exec()

    def closeEvent(self, event):
        """À la fermeture : déconnexion du bridge (multimètre, générateur), alimentation, terminal série, oscilloscope."""
        self._connection_bridge.close()
        if hasattr(self, "_power_supply_view") and self._power_supply_view is not None:
            if hasattr(self._power_supply_view, "_disconnect"):
                self._power_supply_view._disconnect()
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view is not None:
            if hasattr(self._serial_terminal_view, "disconnect_serial"):
                self._serial_terminal_view.disconnect_serial()
        if hasattr(self, "_oscilloscope_view") and self._oscilloscope_view is not None:
            if hasattr(self._oscilloscope_view, "_disconnect"):
                self._oscilloscope_view._disconnect()
        super().closeEvent(event)
