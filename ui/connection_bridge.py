"""
Pont de connexion série (2 équipements : multimètre, générateur).

Isole la logique connexion actuelle pour permettre plus tard de la remplacer
par le ConnectionController / BenchConnectionState (Phase 3).
Voir docs/EVOLUTION_4_EQUIPEMENTS.md (Phase 1bis).
"""
from __future__ import annotations

from typing import Any, Optional

try:
    from config.settings import (
        get_serial_multimeter_config,
        get_serial_generator_config,
        get_filter_test_config,
    )
except ImportError:
    get_serial_multimeter_config = get_serial_generator_config = get_filter_test_config = None

try:
    from core.serial_connection import SerialConnection
    from core.scpi_protocol import ScpiProtocol
    from core.measurement import Measurement
    from core.fy6900_protocol import Fy6900Protocol
    from core.filter_test import FilterTest, FilterTestConfig
    from core.data_logger import DataLogger
except ImportError:
    SerialConnection = ScpiProtocol = Measurement = Fy6900Protocol = None
    FilterTest = FilterTestConfig = DataLogger = None

try:
    from core.serial_exchange_logger import SerialExchangeLogger
except ImportError:
    SerialExchangeLogger = None

try:
    from core.equipment import EquipmentKind, equipment_display_name
except ImportError:
    EquipmentKind = None
    equipment_display_name = None


class ConnectionBridgeState:
    """État exposé par le bridge pour la barre de statut (2 équipements)."""

    __slots__ = (
        "multimeter_connected",
        "multimeter_port",
        "multimeter_name",
        "generator_connected",
        "generator_port",
        "generator_name",
    )

    def __init__(
        self,
        *,
        multimeter_connected: bool = False,
        multimeter_port: str = "?",
        multimeter_name: str = "XDM",
        generator_connected: bool = False,
        generator_port: str = "?",
        generator_name: str = "FY6900",
    ):
        self.multimeter_connected = multimeter_connected
        self.multimeter_port = multimeter_port
        self.multimeter_name = multimeter_name
        self.generator_connected = generator_connected
        self.generator_port = generator_port
        self.generator_name = generator_name


class MainWindowConnectionBridge:
    """
    Logique de connexion série pour 2 équipements (multimètre, générateur).
    MainWindow délègue ici la création des connexions, l'ouverture et la vérification.
    Plus tard (Phase 3) on pourra remplacer l'usage de ce bridge par CallbackConnectionController.
    """

    def __init__(self) -> None:
        self._multimeter_conn: Any = None
        self._generator_conn: Any = None
        self._scpi: Any = None
        self._measurement: Any = None
        self._fy6900: Any = None
        self._filter_test: Any = None
        self._data_logger: Any = None
        self._serial_exchange_logger: Any = None
        self._last_config: dict = {}

    def reconnect(self, config: dict) -> None:
        """
        Ferme les ports existants, recrée les connexions à partir de config,
        ouvre les ports et vérifie que les appareils répondent.
        """
        self.close()
        if not all([SerialConnection, ScpiProtocol, Measurement, Fy6900Protocol, FilterTest, FilterTestConfig]):
            return
        sm = (get_serial_multimeter_config(config) or {}) if get_serial_multimeter_config else {}
        sg = (get_serial_generator_config(config) or {}) if get_serial_generator_config else {}
        ft_cfg = (get_filter_test_config(config) or {}) if get_filter_test_config else {}

        if SerialExchangeLogger and self._serial_exchange_logger is None:
            log_dir = config.get("logging", {}).get("output_dir", "./logs")
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

        if DataLogger:
            self._data_logger = DataLogger()
            self._data_logger.set_measurement(self._measurement)

        self._last_config = config
        self._open_ports()
        self._verify_connections()

    def _open_ports(self) -> None:
        """Ouvre les ports série."""
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

    def _verify_connections(self) -> None:
        """Vérifie que les appareils répondent (IDN? / FY6900)."""
        if not self._multimeter_conn or not self._scpi:
            return
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
        generator_ok = False
        if self._generator_conn.is_open():
            try:
                self._fy6900.set_output(False)
                generator_ok = True
            except Exception:
                pass
        if not generator_ok and self._generator_conn.is_open():
            self._generator_conn.close()

    def get_state(self) -> ConnectionBridgeState:
        """Retourne l'état des connexions pour la barre de statut (utilise la config du dernier reconnect)."""
        sm = (get_serial_multimeter_config(self._last_config) or {}) if get_serial_multimeter_config else {}
        sg = (get_serial_generator_config(self._last_config) or {}) if get_serial_generator_config else {}
        return ConnectionBridgeState(
            multimeter_connected=bool(self._multimeter_conn and self._multimeter_conn.is_open()),
            multimeter_port=sm.get("port", "?"),
            multimeter_name="XDM",
            generator_connected=bool(self._generator_conn and self._generator_conn.is_open()),
            generator_port=sg.get("port", "?"),
            generator_name="FY6900",
        )

    def close(self) -> None:
        """Ferme les connexions série (multimètre et générateur)."""
        if self._multimeter_conn:
            try:
                self._multimeter_conn.close()
            except Exception:
                pass
            self._multimeter_conn = None
        if self._generator_conn:
            try:
                self._generator_conn.close()
            except Exception:
                pass
            self._generator_conn = None
        self._scpi = None
        self._measurement = None
        self._fy6900 = None
        self._filter_test = None
        self._data_logger = None
        # On garde _serial_exchange_logger pour la session

    # Accesseurs pour les vues (MainWindow appelle après reconnect puis _inject_views)

    def get_multimeter_conn(self) -> Any:
        return self._multimeter_conn

    def get_generator_conn(self) -> Any:
        return self._generator_conn

    def get_scpi(self) -> Any:
        return self._scpi

    def get_measurement(self) -> Any:
        return self._measurement

    def get_fy6900(self) -> Any:
        return self._fy6900

    def get_filter_test(self) -> Any:
        return self._filter_test

    def get_data_logger(self) -> Any:
        return self._data_logger

    def get_serial_exchange_logger(self) -> Optional[Any]:
        return self._serial_exchange_logger

    def get_connected_equipment_for_terminal(self) -> list:
        """
        Retourne la liste des équipements connectés utilisables par le terminal série.
        Chaque élément : (kind, display_name, connection) avec connection ayant read/write/is_open.
        Phase 4 : seul le multimètre et le générateur sont gérés par le bridge.
        """
        result = []
        if EquipmentKind is None or equipment_display_name is None:
            return result
        if self._multimeter_conn and self._multimeter_conn.is_open():
            result.append((EquipmentKind.MULTIMETER, equipment_display_name(EquipmentKind.MULTIMETER), self._multimeter_conn))
        if self._generator_conn and self._generator_conn.is_open():
            result.append((EquipmentKind.GENERATOR, equipment_display_name(EquipmentKind.GENERATOR), self._generator_conn))
        return result
