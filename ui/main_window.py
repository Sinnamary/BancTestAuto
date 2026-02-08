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
    QApplication,
)
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut

from ui.widgets import ConnectionStatusBar
from ui.views import MeterView, GeneratorView, LoggingView, FilterTestView, PowerSupplyView, SerialTerminalView
from ui.dialogs import DeviceDetectionDialog, SerialConfigDialog, ViewConfigDialog, ViewLogDialog, HelpDialog, AboutDialog, BodeGraphDialog
from ui.theme_loader import get_theme_stylesheet

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


class DetectionWorker(QThread):
    """Thread pour la détection des équipements (évite de bloquer l'UI)."""
    result = pyqtSignal(object, object, object, object)  # m_port, m_baud, g_port, g_baud

    def run(self):
        if detect_devices is None:
            self.result.emit(None, None, None, None)
            return
        m_port, m_baud, g_port, g_baud, _log_lines = detect_devices()
        self.result.emit(m_port, m_baud, g_port, g_baud)


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
        self._setup_shortcuts()
        # Pas d'ouverture de ports au démarrage : utiliser "Charger config" ou "Détecter" pour connecter
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
        self._power_supply_view = PowerSupplyView()
        self._tabs.addTab(self._power_supply_view, "Alimentation")
        self._serial_terminal_view = SerialTerminalView()
        self._tabs.addTab(self._serial_terminal_view, "Terminal série")
        layout.addWidget(self._tabs)

        self.setCentralWidget(central)

    def _build_statusbar(self):
        pass  # optionnel

    def _connect_connection_bar(self):
        self._connection_bar.get_load_config_button().clicked.connect(self._on_load_config_clicked)
        self._connection_bar.get_params_button().clicked.connect(self._on_params)
        self._connection_bar.get_detect_button().clicked.connect(self._on_detect_clicked)

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
            sm["log_callback"] = self._serial_exchange_logger.get_callback(
                "multimeter", port=sm.get("port"), baudrate=sm.get("baudrate")
            )
            sg["log_callback"] = self._serial_exchange_logger.get_callback(
                "generator", port=sg.get("port"), baudrate=sg.get("baudrate")
            )

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
                points_per_decade=ft_cfg.get("points_per_decade", 10),
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

        # _inject_views() est appelée par l'appelant (__init__ ou _reconnect_serial) pour éviter de l'exécuter deux fois

    def _inject_views(self):
        """Passe les références core aux vues (multimètre, générateur, enregistrement)."""
        meter = self._tabs.widget(0)
        if hasattr(meter, "set_measurement") and self._measurement:
            meter.set_measurement(self._measurement)
        if hasattr(meter, "load_config") and self._config:
            meter.load_config(self._config)
        gen = self._tabs.widget(1)
        if hasattr(gen, "set_fy6900") and self._fy6900:
            gen.set_fy6900(self._fy6900)
        logging_view = self._tabs.widget(2)
        if hasattr(logging_view, "set_data_logger") and self._data_logger:
            logging_view.set_data_logger(self._data_logger)
        if hasattr(logging_view, "load_config") and self._config:
            logging_view.load_config(self._config)
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "load_config") and self._config:
            self._serial_terminal_view.load_config(self._config)

    def _init_views_without_connections(self):
        """Initialise les vues sans créer ni ouvrir de connexion série (aucun port ouvert au démarrage)."""
        if self._config and self._filter_test_view:
            self._filter_test_view.load_config(self._config)
            self._filter_test_view.set_filter_test(None)
        logging_view = self._tabs.widget(2) if self._tabs.count() > 2 else None
        if logging_view and hasattr(logging_view, "load_config") and self._config:
            logging_view.load_config(self._config)
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view and hasattr(self._serial_terminal_view, "load_config") and self._config:
            self._serial_terminal_view.load_config(self._config)

    def _reconnect_serial(self):
        """Ferme les ports, recrée les connexions, ouvre et vérifie les appareils (Charger config / Détecter / Paramètres OK)."""
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

    def _on_load_config_clicked(self):
        """Bouton Charger config : récupère config.json et tente de se connecter aux équipements."""
        if not load_config:
            QMessageBox.warning(self, "Config", "Chargement de la config non disponible.")
            return
        try:
            config_path = get_config_file_path() if get_config_file_path else Path("config/config.json")
            if not config_path.exists():
                QMessageBox.warning(
                    self,
                    "Charger config",
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
            sm = get_serial_multimeter_config(self._config) if get_serial_multimeter_config else {}
            sg = get_serial_generator_config(self._config) if get_serial_generator_config else {}
            msg = f"Config : {config_path.name} — Multimètre {sm.get('port', '?')} @ {sm.get('baudrate', '?')} bauds, Générateur {sg.get('port', '?')} @ {sg.get('baudrate', '?')} bauds."
            if self.statusBar():
                self.statusBar().showMessage(msg)
            logger.info("Config rechargée depuis %s", config_path)
        except Exception as e:
            logger.exception("Charger config")
            QMessageBox.warning(
                self,
                "Charger config",
                f"Impossible de charger la config : {e}",
            )

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

    def _on_detection_result(self, multimeter_port, multimeter_baud, generator_port, generator_baud):
        logger.info("Détection: multimètre=%s@%s, générateur=%s@%s", multimeter_port, multimeter_baud, generator_port, generator_baud)
        self._config = update_config_ports(
            self._config,
            multimeter_port,
            generator_port,
            multimeter_baud=multimeter_baud,
            generator_baud=generator_baud,
        )
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
        dlg = DeviceDetectionDialog(
            self,
            config=self._config,
            on_config_updated=self._on_detection_config_updated,
        )
        dlg.exec()

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

    def _on_params(self):
        """Ouvre la configuration série : affiche les valeurs lues depuis config.json.
        OK = applique les champs du formulaire en mémoire et reconnecte.
        Fichier → Sauvegarder config pour écrire dans config.json."""
        config_from_file = load_config() if load_config else self._config
        dlg = SerialConfigDialog(config=config_from_file, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._config = dlg.get_updated_config()
            self._reconnect_serial()
            if self.statusBar():
                self.statusBar().showMessage(
                    "Configuration série appliquée. Fichier → Sauvegarder config pour écrire config.json."
                )

    def _on_open_bode_csv(self):
        """Ouvre un fichier CSV Banc filtre et affiche le graphique Bode."""
        default_dir = Path("datas/csv") if Path("datas/csv").exists() else Path(".")
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir CSV Banc filtre", str(default_dir),
            "CSV (*.csv);;Tous (*)"
        )
        if not path:
            return
        try:
            points = self._load_bode_csv(path)
            if not points:
                QMessageBox.warning(
                    self, "CSV Banc filtre",
                    "Aucune donnée valide trouvée dans le fichier. Format attendu : f_Hz;Us_V;Us_Ue;Gain_dB",
                )
                return
            dlg = BodeGraphDialog(self, points=points)
            dlg.setWindowTitle(f"Graphique Bode — {Path(path).name}")
            dlg.exec()
        except Exception as e:
            logger.exception("Chargement CSV Banc filtre")
            QMessageBox.warning(self, "CSV Banc filtre", f"Erreur lors du chargement : {e}")

    def _load_bode_csv(self, path: str) -> list:
        """Charge un CSV Banc filtre et retourne une liste de BodePoint."""
        if BodePoint is None:
            return []
        import csv as csv_module
        points = []
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv_module.reader(f, delimiter=";")
            header = next(reader, None)
            if not header:
                return []
            # Colonnes attendues : f_Hz, Us_V, Us_Ue, Gain_dB
            col_map = {}
            for i, col in enumerate(header):
                c = col.strip().lower().replace(" ", "")
                if "f_hz" in c or "fhz" in c:
                    col_map["f_hz"] = i
                elif "us_v" in c:
                    col_map["us_v"] = i
                elif "us_ue" in c or "us/ue" in c or "gain_linear" in c:
                    col_map["gain_linear"] = i
                elif "gain_db" in c or ("gain" in c and "db" in c):
                    col_map["gain_db"] = i
            if "f_hz" not in col_map or "gain_db" not in col_map:
                col_map = {"f_hz": 0, "us_v": 1, "gain_linear": 2, "gain_db": 3}
            for row in reader:
                if len(row) < 4:
                    continue
                try:
                    idx_f = col_map["f_hz"]
                    idx_us = col_map.get("us_v", 1)
                    idx_glin = col_map.get("gain_linear", 2)
                    idx_gdb = col_map["gain_db"]
                    f_hz = float(row[idx_f].replace(",", "."))
                    us_v = float(row[idx_us].replace(",", ".")) if idx_us < len(row) else 0.0
                    g_db = float(row[idx_gdb].replace(",", "."))
                    g_lin = float(row[idx_glin].replace(",", ".")) if idx_glin < len(row) else (10 ** (g_db / 20.0) if g_db > -200 else 0.0)
                    points.append(BodePoint(f_hz=f_hz, us_v=us_v, gain_linear=g_lin, gain_db=g_db))
                except (ValueError, IndexError, KeyError):
                    continue
        return points

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
        """À la fermeture : déconnexion de l'alimentation et du terminal série."""
        if hasattr(self, "_power_supply_view") and self._power_supply_view is not None:
            if hasattr(self._power_supply_view, "_disconnect"):
                self._power_supply_view._disconnect()
        if hasattr(self, "_serial_terminal_view") and self._serial_terminal_view is not None:
            if hasattr(self._serial_terminal_view, "disconnect_serial"):
                self._serial_terminal_view.disconnect_serial()
        super().closeEvent(event)
