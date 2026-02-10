"""
Panneau de connexion DOS1102 : mode Série / USB, port, liste USB, bouton Connexion, statut.
Réutilisable : ne crée pas la connexion, notifie le parent via callbacks.
"""
from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QMessageBox,
    QWidget,
)


def list_serial_ports() -> list[str]:
    try:
        import serial.tools.list_ports
        return [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        return []


class OscilloscopeConnectionPanel(QWidget):
    """
    Panneau connexion oscilloscope.
    Callbacks : on_connect_serial(port), on_connect_usb(vid, pid), on_disconnect().
    Le parent effectue la connexion puis appelle set_connected(True, status_text).
    """

    DEFAULT_BAUD = 115200

    def __init__(
        self,
        parent=None,
        *,
        on_connect_serial: Optional[Callable[[str], None]] = None,
        on_connect_usb: Optional[Callable[[int, int], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self._on_connect_serial = on_connect_serial
        self._on_connect_usb = on_connect_usb
        self._on_disconnect = on_disconnect
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        gb = QGroupBox("Connexion (DOS1102)")
        conn_layout = QHBoxLayout(gb)

        conn_layout.addWidget(QLabel("Mode:"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Série (COM)", "USB (WinUSB/PyUSB)"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        conn_layout.addWidget(self._mode_combo)

        self._port_label = QLabel("Port:")
        conn_layout.addWidget(self._port_label)
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setEditable(True)
        conn_layout.addWidget(self._port_combo)

        self._speed_label = QLabel(f"Vitesse: {self.DEFAULT_BAUD}")
        conn_layout.addWidget(self._speed_label)

        self._usb_combo = QComboBox()
        self._usb_combo.setMinimumWidth(220)
        self._usb_combo.setPlaceholderText("Rafraîchir pour lister les périphériques")
        conn_layout.addWidget(self._usb_combo)

        self._usb_refresh_btn = QPushButton("Rafraîchir USB")
        self._usb_refresh_btn.clicked.connect(self._refresh_usb)
        conn_layout.addWidget(self._usb_refresh_btn)

        self._connect_btn = QPushButton("Connexion")
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        conn_layout.addWidget(self._connect_btn)

        from ui.widgets import StatusIndicator
        self._status_indicator = StatusIndicator(False, self)
        conn_layout.addWidget(self._status_indicator)

        self._status_label = QLabel("Déconnecté")
        conn_layout.addWidget(self._status_label)
        conn_layout.addStretch()

        layout.addWidget(gb)
        self._on_mode_changed()

    def _on_mode_changed(self) -> None:
        is_serial = self._mode_combo.currentIndex() == 0
        self._port_label.setVisible(is_serial)
        self._port_combo.setVisible(is_serial)
        self._speed_label.setVisible(is_serial)
        self._usb_combo.setVisible(not is_serial)
        self._usb_refresh_btn.setVisible(not is_serial)
        if not is_serial and self._usb_combo.count() == 0:
            self._refresh_usb()

    def _refresh_usb(self) -> None:
        try:
            from core.dos1102_usb_connection import list_usb_devices
        except ImportError:
            QMessageBox.warning(
                self, "Oscilloscope",
                "PyUSB non disponible. Installez : pip install pyusb\n"
                "Sous Windows, installez aussi le backend libusb et le pilote WinUSB (Zadig).",
            )
            return
        self._usb_combo.clear()
        devices = list_usb_devices()
        if not devices:
            self._usb_combo.addItem("Aucun périphérique USB trouvé", (None, None))
            return
        for vid, pid, desc in devices:
            self._usb_combo.addItem(desc, (vid, pid))
        self._usb_combo.setCurrentIndex(0)

    def _on_connect_clicked(self) -> None:
        if self._connect_btn.text() == "Déconnexion":
            if self._on_disconnect:
                self._on_disconnect()
            return
        if self._mode_combo.currentIndex() == 0:
            port = self._port_combo.currentText().strip()
            if not port:
                QMessageBox.warning(self, "Oscilloscope", "Choisissez un port série.")
                return
            if self._on_connect_serial:
                self._on_connect_serial(port)
        else:
            data = self._usb_combo.currentData()
            if not data or data[0] is None:
                QMessageBox.warning(
                    self, "Oscilloscope",
                    "Choisissez un périphérique USB (Rafraîchir USB si vide).",
                )
                return
            vid, pid = data
            if self._on_connect_usb:
                self._on_connect_usb(vid, pid)

    def refresh_ports(self) -> None:
        current = self._port_combo.currentText()
        self._port_combo.clear()
        ports = list_serial_ports()
        if ports:
            self._port_combo.addItems(ports)
        if current and (current in ports or not ports):
            self._port_combo.setCurrentText(current)
        elif self._port_combo.count() > 0:
            self._port_combo.setCurrentIndex(0)

    def set_connected(self, connected: bool, status_text: str = "") -> None:
        self._status_indicator.set_connected(connected)
        self._status_label.setText(status_text or ("Connecté" if connected else "Déconnecté"))
        self._connect_btn.setText("Déconnexion" if connected else "Connexion")
        self._mode_combo.setEnabled(not connected)
        self._port_combo.setEnabled(not connected)
        self._usb_combo.setEnabled(not connected)
        self._usb_refresh_btn.setEnabled(not connected)

    def get_port(self) -> str:
        return self._port_combo.currentText().strip()

    def get_usb_selection(self) -> Optional[tuple[int, int]]:
        data = self._usb_combo.currentData()
        if not data or data[0] is None:
            return None
        return (data[0], data[1])

    def is_serial_mode(self) -> bool:
        return self._mode_combo.currentIndex() == 0

    def set_port(self, port: str) -> None:
        self._port_combo.setCurrentText(port)
