"""
Vue onglet Oscilloscope HANMATEK DOS1102 — composition des panels.
Connexion et protocole gérés ici ; les panels sont réutilisables.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from .connection_panel import OscilloscopeConnectionPanel
from .acquisition_trigger_panel import OscilloscopeAcqTriggerPanel
from .measurement_panel import OscilloscopeMeasurementPanel
from .waveform_panel import OscilloscopeWaveformPanel
from .channels_panel import OscilloscopeChannelsPanel


class OscilloscopeView(QWidget):
    """Onglet Oscilloscope DOS1102 : connexion + panels acquisition, mesures, forme d'onde, canaux."""

    DEFAULT_BAUD = 115200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn = None
        self._protocol = None
        self._panels: list[QWidget] = []
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        self._conn_panel = OscilloscopeConnectionPanel(
            self,
            on_connect_serial=self._connect_serial,
            on_connect_usb=self._connect_usb,
            on_disconnect=self._disconnect,
        )
        layout.addWidget(self._conn_panel)

        self._acq_trig_panel = OscilloscopeAcqTriggerPanel(self)
        self._panels.append(self._acq_trig_panel)
        layout.addWidget(self._acq_trig_panel)

        self._meas_panel = OscilloscopeMeasurementPanel(self)
        self._panels.append(self._meas_panel)
        layout.addWidget(self._meas_panel)

        self._waveform_panel = OscilloscopeWaveformPanel(self)
        self._panels.append(self._waveform_panel)
        layout.addWidget(self._waveform_panel)

        self._channels_panel = OscilloscopeChannelsPanel(self)
        self._panels.append(self._channels_panel)
        layout.addWidget(self._channels_panel)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _update_panels_protocol(self, protocol) -> None:
        for p in self._panels:
            if hasattr(p, "set_protocol"):
                p.set_protocol(protocol)

    def _update_panels_connected(self, connected: bool) -> None:
        for p in self._panels:
            if hasattr(p, "set_connected"):
                p.set_connected(connected)

    def _connect_serial(self, port: str) -> None:
        try:
            from core.serial_connection import SerialConnection
            from core.dos1102_protocol import Dos1102Protocol

            self._conn = SerialConnection(
                port=port,
                baudrate=self.DEFAULT_BAUD,
                timeout=2.0,
                write_timeout=2.0,
            )
            self._conn.open()
            self._protocol = Dos1102Protocol(self._conn)
            self._on_connect_success()
        except Exception as e:
            self._cleanup_connection()
            QMessageBox.warning(self, "Oscilloscope", f"Impossible de se connecter (série) : {e}")

    def _connect_usb(self, vid: int, pid: int) -> None:
        try:
            from core.dos1102_usb_connection import Dos1102UsbConnection
            from core.dos1102_protocol import Dos1102Protocol

            self._conn = Dos1102UsbConnection(id_vendor=vid, id_product=pid)
            self._conn.open()
            self._protocol = Dos1102Protocol(self._conn)
            self._on_connect_success()
        except Exception as e:
            self._cleanup_connection()
            QMessageBox.warning(
                self, "Oscilloscope",
                f"Impossible de se connecter (USB) : {e}\n\n"
                "Vérifiez le pilote WinUSB (Zadig).",
            )

    def _on_connect_success(self) -> None:
        try:
            idn = self._protocol.idn()
            status = f"Connecté — {idn[:40]}" if idn else "Connecté"
        except Exception:
            status = "Connecté"
        self._conn_panel.set_connected(True, status)
        self._update_panels_protocol(self._protocol)
        self._update_panels_connected(True)

    def _cleanup_connection(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._protocol = None
        self._update_panels_protocol(None)

    def _disconnect(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._protocol = None
        self._conn_panel.set_connected(False, "Déconnecté")
        self._update_panels_protocol(None)
        self._update_panels_connected(False)
        if hasattr(self._meas_panel, "set_result"):
            self._meas_panel.set_result("—")
        if hasattr(self._meas_panel, "set_general_result"):
            self._meas_panel.set_general_result("—")

    def load_config(self, config: dict) -> None:
        """Remplit le port depuis config.serial_oscilloscope."""
        osc = config.get("serial_oscilloscope") or {}
        port = (osc.get("port") or "").strip()
        if port:
            self._conn_panel.set_port(port)
        self._conn_panel.refresh_ports()

    def get_current_serial_port(self) -> str | None:
        """Port série actuellement sélectionné (mode Série uniquement), sinon None."""
        if self._conn_panel.is_serial_mode():
            port = self._conn_panel.get_port().strip()
            return port or None
        return None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._conn_panel.refresh_ports()

    def closeEvent(self, event) -> None:
        self._disconnect()
        super().closeEvent(event)
