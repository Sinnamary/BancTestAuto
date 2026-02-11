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
        get_serial_power_supply_config,
        get_usb_oscilloscope_config,
        get_filter_test_config,
    )
except ImportError:
    get_serial_multimeter_config = get_serial_generator_config = get_filter_test_config = None
    get_serial_power_supply_config = get_usb_oscilloscope_config = None

try:
    from core.serial_connection import SerialConnection
    from core.scpi_protocol import ScpiProtocol
    from core.measurement import Measurement
    from core.fy6900_protocol import Fy6900Protocol
    from core.filter_test import FilterTest, FilterTestConfig
    from core.data_logger import DataLogger
    from core.bode_measure_source import MultimeterBodeAdapter, OscilloscopeBodeSource, SwitchableBodeMeasureSource
    from core.dos1102_protocol import Dos1102Protocol
except ImportError:
    SerialConnection = ScpiProtocol = Measurement = Fy6900Protocol = None
    FilterTest = FilterTestConfig = DataLogger = None
    MultimeterBodeAdapter = OscilloscopeBodeSource = SwitchableBodeMeasureSource = None
    Dos1102Protocol = None

try:
    from core.serial_exchange_logger import SerialExchangeLogger
except ImportError:
    SerialExchangeLogger = None

try:
    from core.equipment import EquipmentKind, equipment_display_name
except ImportError:
    EquipmentKind = None
    equipment_display_name = None

try:
    from core.dos1102_usb_connection import Dos1102UsbConnection
except ImportError:
    Dos1102UsbConnection = None

try:
    from core.app_logger import get_logger
except ImportError:
    def get_logger(_name):
        import logging
        return logging.getLogger(_name)

logger = get_logger(__name__)


class ConnectionBridgeState:
    """État exposé par le bridge pour la barre de statut (4 équipements)."""

    __slots__ = (
        "multimeter_connected",
        "multimeter_port",
        "multimeter_name",
        "generator_connected",
        "generator_port",
        "generator_name",
        "power_supply_connected",
        "power_supply_port",
        "oscilloscope_connected",
        "oscilloscope_label",
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
        power_supply_connected: bool = False,
        power_supply_port: str = "?",
        oscilloscope_connected: bool = False,
        oscilloscope_label: str = "USB",
    ):
        self.multimeter_connected = multimeter_connected
        self.multimeter_port = multimeter_port
        self.multimeter_name = multimeter_name
        self.generator_connected = generator_connected
        self.generator_port = generator_port
        self.generator_name = generator_name
        self.power_supply_connected = power_supply_connected
        self.power_supply_port = power_supply_port
        self.oscilloscope_connected = oscilloscope_connected
        self.oscilloscope_label = oscilloscope_label


class MainWindowConnectionBridge:
    """
    Logique de connexion série pour 2 équipements (multimètre, générateur).
    MainWindow délègue ici la création des connexions, l'ouverture et la vérification.
    Plus tard (Phase 3) on pourra remplacer l'usage de ce bridge par CallbackConnectionController.
    """

    def __init__(self) -> None:
        self._multimeter_conn: Any = None
        self._generator_conn: Any = None
        self._power_supply_conn: Any = None
        self._oscilloscope_conn: Any = None
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

        # Le fichier serial_*.log est réservé au terminal série (voir SerialTerminalView).

        self._multimeter_conn = SerialConnection(**sm)
        self._generator_conn = SerialConnection(**sg)

        # Alimentation (RS305P) — optionnel
        sp = (get_serial_power_supply_config(config) or {}) if get_serial_power_supply_config else {}
        if sp and SerialConnection:
            self._power_supply_conn = SerialConnection(**sp)
            logger.debug("Bridge: alimentation configurée sur %s @ %s bauds", sp.get("port", "?"), sp.get("baudrate"))
        else:
            self._power_supply_conn = None
            if not sp:
                logger.debug("Bridge: pas de config serial_power_supply — alimentation non connectée")

        # Oscilloscope USB (DOS1102) — optionnel
        usb_cfg = (get_usb_oscilloscope_config(config) or {}) if get_usb_oscilloscope_config else {}
        vid = usb_cfg.get("vendor_id")
        pid = usb_cfg.get("product_id")
        if (
            Dos1102UsbConnection
            and isinstance(vid, int)
            and isinstance(pid, int)
            and vid != 0
            and pid != 0
        ):
            self._oscilloscope_conn = Dos1102UsbConnection(
                vid,
                pid,
                read_timeout_ms=usb_cfg.get("read_timeout_ms", 5000),
                write_timeout_ms=usb_cfg.get("write_timeout_ms", 2000),
            )
        else:
            self._oscilloscope_conn = None

        self._scpi = ScpiProtocol(self._multimeter_conn)
        self._measurement = Measurement(self._scpi)
        self._fy6900 = Fy6900Protocol(self._generator_conn)
        # Source de mesure banc filtre : switchable multimètre / oscilloscope (Phase 3)
        multimeter_adapter = MultimeterBodeAdapter(self._measurement) if MultimeterBodeAdapter else None
        measure_source = None
        if multimeter_adapter is not None and SwitchableBodeMeasureSource is not None:
            measure_source = SwitchableBodeMeasureSource(multimeter_adapter, self._make_oscilloscope_bode_source)
        elif multimeter_adapter is not None:
            measure_source = multimeter_adapter
        self._filter_test = None
        if FilterTest and measure_source is not None:
            self._filter_test = FilterTest(
                self._fy6900,
                measure_source,
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
        elif FilterTest and not measure_source:
            logger.warning("Bridge: MultimeterBodeAdapter non disponible, banc filtre désactivé")

        if DataLogger:
            self._data_logger = DataLogger()
            self._data_logger.set_measurement(self._measurement)

        self._last_config = config
        self._open_ports()
        self._verify_connections()

    def _open_ports(self) -> None:
        """Ouvre les ports série et la connexion USB oscilloscope."""
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
        try:
            if self._power_supply_conn:
                self._power_supply_conn.open()
                logger.debug("Bridge: alimentation ouverte")
        except Exception as e:
            logger.warning("Bridge: échec ouverture alimentation — %s", e)
        try:
            if self._oscilloscope_conn:
                self._oscilloscope_conn.open()
                logger.debug("Bridge: oscilloscope USB ouvert")
        except Exception as e:
            logger.warning("Bridge: échec ouverture oscilloscope USB — %s", e)

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
        """Retourne l'état des 4 connexions pour la barre de statut."""
        sm = (get_serial_multimeter_config(self._last_config) or {}) if get_serial_multimeter_config else {}
        sg = (get_serial_generator_config(self._last_config) or {}) if get_serial_generator_config else {}
        sp = (get_serial_power_supply_config(self._last_config) or {}) if get_serial_power_supply_config else {}
        usb_cfg = (get_usb_oscilloscope_config(self._last_config) or {}) if get_usb_oscilloscope_config else {}
        oscillo_open = bool(self._oscilloscope_conn and getattr(self._oscilloscope_conn, "is_open", lambda: False)())
        oscillo_label = "USB"
        if usb_cfg.get("vendor_id") is not None and usb_cfg.get("product_id") is not None:
            oscillo_label = f"0x{usb_cfg['vendor_id']:04X}:0x{usb_cfg['product_id']:04X}"
        return ConnectionBridgeState(
            multimeter_connected=bool(self._multimeter_conn and self._multimeter_conn.is_open()),
            multimeter_port=sm.get("port", "?"),
            multimeter_name="XDM",
            generator_connected=bool(self._generator_conn and self._generator_conn.is_open()),
            generator_port=sg.get("port", "?"),
            generator_name="FY6900",
            power_supply_connected=bool(self._power_supply_conn and self._power_supply_conn.is_open()),
            power_supply_port=sp.get("port", "?"),
            oscilloscope_connected=oscillo_open,
            oscilloscope_label=oscillo_label,
        )

    def close(self) -> None:
        """Ferme les 4 connexions (multimètre, générateur, alimentation, oscilloscope)."""
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
        if self._power_supply_conn:
            try:
                self._power_supply_conn.close()
            except Exception:
                pass
            self._power_supply_conn = None
        if self._oscilloscope_conn:
            try:
                self._oscilloscope_conn.close()
            except Exception:
                pass
            self._oscilloscope_conn = None
        self._scpi = None
        self._measurement = None
        self._fy6900 = None
        self._filter_test = None
        self._data_logger = None
        # On garde _serial_exchange_logger pour la session

    # Accesseurs pour les vues (MainWindow appelle après reconnect puis _inject_views)

    def _make_oscilloscope_bode_source(self) -> Any:
        """Crée la source Bode oscilloscope si l'oscillo est connecté (pour SwitchableBodeMeasureSource)."""
        if not self._oscilloscope_conn or not getattr(self._oscilloscope_conn, "is_open", lambda: False)():
            return None
        if OscilloscopeBodeSource is None or Dos1102Protocol is None:
            return None
        ft_cfg = (get_filter_test_config(self._last_config) or {}) if get_filter_test_config and self._last_config else {}
        ch_ue = int(ft_cfg.get("oscillo_channel_ue", 1))
        ch_us = int(ft_cfg.get("oscillo_channel_us", 2))
        return OscilloscopeBodeSource(Dos1102Protocol(self._oscilloscope_conn), channel_ue=ch_ue, channel_us=ch_us)

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

    def get_power_supply_conn(self) -> Any:
        return self._power_supply_conn

    def get_oscilloscope_conn(self) -> Any:
        return self._oscilloscope_conn

    def get_connected_equipment_for_terminal(self) -> list:
        """
        Retourne la liste des équipements connectés utilisables par le terminal série.
        Chaque élément : (kind, display_name, connection, détail) avec détail = port (ex. COM17) ou libellé USB.
        """
        result = []
        if EquipmentKind is None or equipment_display_name is None:
            return result
        state = self.get_state()
        if self._multimeter_conn and self._multimeter_conn.is_open():
            result.append((EquipmentKind.MULTIMETER, equipment_display_name(EquipmentKind.MULTIMETER), self._multimeter_conn, state.multimeter_port or "?"))
        if self._generator_conn and self._generator_conn.is_open():
            result.append((EquipmentKind.GENERATOR, equipment_display_name(EquipmentKind.GENERATOR), self._generator_conn, state.generator_port or "?"))
        if self._power_supply_conn and self._power_supply_conn.is_open():
            result.append((EquipmentKind.POWER_SUPPLY, equipment_display_name(EquipmentKind.POWER_SUPPLY), self._power_supply_conn, state.power_supply_port or "?"))
        if self._oscilloscope_conn and getattr(self._oscilloscope_conn, "is_open", lambda: False)():
            result.append((EquipmentKind.OSCILLOSCOPE, equipment_display_name(EquipmentKind.OSCILLOSCOPE), self._oscilloscope_conn, state.oscilloscope_label or "USB"))
        return result
