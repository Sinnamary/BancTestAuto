"""
Vue onglet Oscilloscope HANMATEK DOS1102 — panels acquisition, mesures, forme d'onde, canaux.
Utilise la connexion déjà établie par le bridge (Connecter tout).
"""
from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from .acquisition_trigger_panel import OscilloscopeAcqTriggerPanel
from .measurement_panel import OscilloscopeMeasurementPanel
from .waveform_panel import OscilloscopeWaveformPanel
from .channels_panel import OscilloscopeChannelsPanel


class OscilloscopeView(QWidget):
    """Onglet Oscilloscope DOS1102. Utilise la connexion du bridge si disponible."""

    scale_changed_from_scope = pyqtSignal(int, float)  # ch, v_per_div (émission thread-safe depuis le balayage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn: Any = None
        self._protocol: Any = None
        self._panels: list[QWidget] = []
        # Config USB (config.json) pour get_current_usb_device / sauvegarde
        self._usb_vendor_id: Optional[int] = None
        self._usb_product_id: Optional[int] = None
        self._usb_read_timeout_ms: Optional[int] = None
        self._usb_write_timeout_ms: Optional[int] = None
        self._build_ui()

    def set_connection(self, conn: Optional[Any], protocol: Optional[Any] = None) -> None:
        """Utilise la connexion et le protocole fournis par le bridge (ou None si déconnecté).
        Si protocol est fourni, il est partagé avec le balayage Bode pour que l'écran Canaux reflète les calibres."""
        old_protocol = self._protocol
        self._conn = None
        self._protocol = None
        if old_protocol is not None and hasattr(old_protocol, "set_on_ch_scale_changed"):
            old_protocol.set_on_ch_scale_changed(None)
        if conn is not None and getattr(conn, "is_open", lambda: False)():
            try:
                if protocol is not None:
                    self._conn = conn
                    self._protocol = protocol
                    self._protocol.idn()
                    if hasattr(self._protocol, "set_on_ch_scale_changed"):
                        self._protocol.set_on_ch_scale_changed(self._emit_scale_changed)
                else:
                    from core.dos1102_protocol import Dos1102Protocol
                    self._conn = conn
                    self._protocol = Dos1102Protocol(conn)
                    self._protocol.idn()
                self._update_panels_protocol(self._protocol)
                self._update_panels_connected(True)
            except Exception:
                self._conn = None
                self._protocol = None
        if self._protocol is None:
            self._update_panels_protocol(None)
            self._update_panels_connected(False)
            if hasattr(self, "_meas_panel") and self._meas_panel:
                if hasattr(self._meas_panel, "set_result"):
                    self._meas_panel.set_result("—")
                if hasattr(self._meas_panel, "set_general_result"):
                    self._meas_panel.set_general_result("—")

    def _emit_scale_changed(self, ch: int, v_per_div: float) -> None:
        """Appelé par le protocole (éventuellement depuis un autre thread) ; émet le signal pour mise à jour UI."""
        self.scale_changed_from_scope.emit(ch, v_per_div)

    def _on_scale_changed_from_scope(self, ch: int, v_per_div: float) -> None:
        """Met à jour l'affichage des calibres dans le panneau Canaux (slot appelé dans le thread UI)."""
        if hasattr(self, "_channels_panel") and self._channels_panel is not None:
            self._channels_panel.set_ch_scale_display(ch, v_per_div)

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        self._acq_trig_panel = OscilloscopeAcqTriggerPanel(self)
        self._panels.append(self._acq_trig_panel)
        layout.addWidget(self._acq_trig_panel)

        self._channels_panel = OscilloscopeChannelsPanel(self)
        self._panels.append(self._channels_panel)
        layout.addWidget(self._channels_panel)

        self._meas_panel = OscilloscopeMeasurementPanel(self)
        self._panels.append(self._meas_panel)
        layout.addWidget(self._meas_panel)

        self._waveform_panel = OscilloscopeWaveformPanel(self)
        self._panels.append(self._waveform_panel)
        layout.addWidget(self._waveform_panel)

        self.scale_changed_from_scope.connect(self._on_scale_changed_from_scope)

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

    def _disconnect(self) -> None:
        """Réinitialise l'état sans fermer la connexion (gérée par le bridge)."""
        self._conn = None
        self._protocol = None
        self._update_panels_protocol(None)
        self._update_panels_connected(False)
        if hasattr(self, "_meas_panel") and self._meas_panel:
            if hasattr(self._meas_panel, "set_result"):
                self._meas_panel.set_result("—")
            if hasattr(self._meas_panel, "set_general_result"):
                self._meas_panel.set_general_result("—")

    def load_config(self, config: dict) -> None:
        """Mémorise les paramètres USB (config.json) pour get_current_usb_device / sauvegarde."""
        usb_cfg = config.get("usb_oscilloscope") or {}
        vid = usb_cfg.get("vendor_id")
        pid = usb_cfg.get("product_id")
        if isinstance(vid, int) and isinstance(pid, int):
            self._usb_vendor_id = vid
            self._usb_product_id = pid
        rt = usb_cfg.get("read_timeout_ms")
        wt = usb_cfg.get("write_timeout_ms")
        if isinstance(rt, int):
            self._usb_read_timeout_ms = rt
        if isinstance(wt, int):
            self._usb_write_timeout_ms = wt

    def get_current_serial_port(self) -> Optional[str]:
        """Plus de port série dans l'onglet ; connexion via bridge (USB)."""
        return None

    def get_current_usb_device(self) -> Optional[tuple[int, int]]:
        """Périphérique USB depuis la config (détection / sauvegarde)."""
        if isinstance(self._usb_vendor_id, int) and isinstance(self._usb_product_id, int):
            return (self._usb_vendor_id, self._usb_product_id)
        return None

    def closeEvent(self, event) -> None:
        self._disconnect()
        super().closeEvent(event)
