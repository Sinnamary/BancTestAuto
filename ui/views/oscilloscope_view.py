"""
Vue onglet Oscilloscope HANMATEK DOS1102 — connexion série, acquisition, canaux, trigger, mesures.
Connexion gérée dans l'onglet ; config serial_oscilloscope pour le port par défaut.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QMessageBox,
    QFormLayout,
    QFrame,
    QScrollArea,
)
from PyQt6.QtCore import Qt


def _list_serial_ports():
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]
    except Exception:
        return []


class StatusIndicator(QFrame):
    """Pastille verte (connecté) ou rouge (déconnecté)."""

    def __init__(self, connected: bool = False, parent=None):
        super().__init__(parent)
        self._connected = connected
        self.setFixedSize(14, 14)
        self._update_style()

    def _update_style(self):
        color = "#2ecc71" if self._connected else "#e74c3c"
        self.setStyleSheet(f"""
            StatusIndicator {{
                border-radius: 7px;
                background-color: {color};
            }}
        """)

    def set_connected(self, connected: bool):
        self._connected = connected
        self._update_style()


# Types de mesure DOS1102 (requêtes :MEAS:CHn:XXX?)
MEAS_TYPES = [
    ("Fréquence", "FREQuency"),
    ("Période", "PERiod"),
    ("Moyenne", "AVERage"),
    ("Crête à crête", "PKPK"),
    ("Max", "MAX"),
    ("Min", "MIN"),
    ("RMS", "TRUERMS"),
    ("Amplitude", "VAMP"),
    ("Sommet", "VTOP"),
    ("Base", "VBASe"),
    ("Temps montée", "RTime"),
    ("Temps descente", "FTime"),
    ("Largeur imp. +", "PWIDth"),
    ("Largeur imp. -", "NWIDth"),
]


class OscilloscopeView(QWidget):
    """Onglet Oscilloscope HANMATEK DOS1102. Connexion série gérée localement."""

    DEFAULT_BAUD = 115200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn = None
        self._protocol = None
        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        conn_gb = QGroupBox("Connexion (DOS1102)")
        conn_layout = QHBoxLayout(conn_gb)
        conn_layout.addWidget(QLabel("Mode:"))
        self._conn_mode_combo = QComboBox()
        self._conn_mode_combo.addItems(["Série (COM)", "USB (WinUSB/PyUSB)"])
        self._conn_mode_combo.currentIndexChanged.connect(self._on_conn_mode_changed)
        conn_layout.addWidget(self._conn_mode_combo)
        self._port_label = QLabel("Port:")
        conn_layout.addWidget(self._port_label)
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setEditable(True)
        conn_layout.addWidget(self._port_combo)
        self._speed_label = QLabel(f"Vitesse: {self.DEFAULT_BAUD}")
        conn_layout.addWidget(self._speed_label)
        self._usb_device_combo = QComboBox()
        self._usb_device_combo.setMinimumWidth(220)
        self._usb_device_combo.setPlaceholderText("Rafraîchir pour lister les périphériques")
        conn_layout.addWidget(self._usb_device_combo)
        self._usb_refresh_btn = QPushButton("Rafraîchir USB")
        self._usb_refresh_btn.clicked.connect(self._refresh_usb_devices)
        conn_layout.addWidget(self._usb_refresh_btn)
        self._connect_btn = QPushButton("Connexion")
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        conn_layout.addWidget(self._connect_btn)
        self._status_indicator = StatusIndicator(False, self)
        conn_layout.addWidget(self._status_indicator)
        self._status_label = QLabel("Déconnecté")
        conn_layout.addWidget(self._status_label)
        conn_layout.addStretch()
        layout.addWidget(conn_gb)
        self._on_conn_mode_changed()

        acq_gb = QGroupBox("Acquisition")
        acq_layout = QHBoxLayout(acq_gb)
        acq_layout.addWidget(QLabel("Mode:"))
        self._acq_combo = QComboBox()
        self._acq_combo.addItems(["SAMP (échantillonnage)", "PEAK (pic)", "AVE (moyenne)"])
        self._acq_combo.setCurrentIndex(0)
        acq_layout.addWidget(self._acq_combo)
        self._acq_apply_btn = QPushButton("Appliquer")
        self._acq_apply_btn.clicked.connect(self._on_acq_apply)
        self._acq_apply_btn.setEnabled(False)
        acq_layout.addWidget(self._acq_apply_btn)
        acq_layout.addStretch()
        layout.addWidget(acq_gb)

        ch_gb = QGroupBox("Canaux")
        ch_layout = QFormLayout(ch_gb)
        ch_layout.addRow(QLabel("Voie 1 — Couplage:"))
        self._ch1_coup_combo = QComboBox()
        self._ch1_coup_combo.addItems(["DC", "AC", "GND"])
        ch_layout.addRow(self._ch1_coup_combo)
        ch_layout.addRow(QLabel("Voie 2 — Couplage:"))
        self._ch2_coup_combo = QComboBox()
        self._ch2_coup_combo.addItems(["DC", "AC", "GND"])
        ch_layout.addRow(self._ch2_coup_combo)
        ch_btn_layout = QHBoxLayout()
        self._ch_apply_btn = QPushButton("Appliquer canaux")
        self._ch_apply_btn.clicked.connect(self._on_ch_apply)
        self._ch_apply_btn.setEnabled(False)
        ch_btn_layout.addWidget(self._ch_apply_btn)
        ch_btn_layout.addStretch()
        ch_layout.addRow("", ch_btn_layout)
        layout.addWidget(ch_gb)

        trig_gb = QGroupBox("Trigger")
        trig_layout = QHBoxLayout(trig_gb)
        self._trig_edge_btn = QPushButton("EDGE")
        self._trig_edge_btn.clicked.connect(lambda: self._set_trigger("EDGE"))
        self._trig_edge_btn.setEnabled(False)
        self._trig_video_btn = QPushButton("VIDEO")
        self._trig_video_btn.clicked.connect(lambda: self._set_trigger("VIDEO"))
        self._trig_video_btn.setEnabled(False)
        trig_layout.addWidget(self._trig_edge_btn)
        trig_layout.addWidget(self._trig_video_btn)
        trig_layout.addStretch()
        layout.addWidget(trig_gb)

        meas_gb = QGroupBox("Mesures")
        meas_layout = QFormLayout(meas_gb)
        meas_layout.addRow(QLabel("Mesure générale (:MEAS?):"))
        self._meas_general_label = QLabel("—")
        meas_layout.addRow(self._meas_general_label)
        meas_layout.addRow(QLabel("Canal:"))
        self._meas_ch_combo = QComboBox()
        self._meas_ch_combo.addItems(["CH1", "CH2"])
        meas_layout.addRow(self._meas_ch_combo)
        meas_layout.addRow(QLabel("Type:"))
        self._meas_type_combo = QComboBox()
        for label, _ in MEAS_TYPES:
            self._meas_type_combo.addItem(label)
        meas_layout.addRow(self._meas_type_combo)
        meas_btn_layout = QHBoxLayout()
        self._meas_query_btn = QPushButton("Mesure générale")
        self._meas_query_btn.clicked.connect(self._on_meas_general)
        self._meas_query_btn.setEnabled(False)
        self._meas_ch_btn = QPushButton("Mesure canal/type")
        self._meas_ch_btn.clicked.connect(self._on_meas_ch)
        self._meas_ch_btn.setEnabled(False)
        meas_btn_layout.addWidget(self._meas_query_btn)
        meas_btn_layout.addWidget(self._meas_ch_btn)
        meas_layout.addRow("", meas_btn_layout)
        meas_layout.addRow(QLabel("Résultat:"))
        self._meas_result_label = QLabel("—")
        meas_layout.addRow(self._meas_result_label)
        layout.addWidget(meas_gb)

        layout.addStretch()

    def _on_conn_mode_changed(self):
        is_serial = self._conn_mode_combo.currentIndex() == 0
        self._port_label.setVisible(is_serial)
        self._port_combo.setVisible(is_serial)
        self._speed_label.setVisible(is_serial)
        self._usb_device_combo.setVisible(not is_serial)
        self._usb_refresh_btn.setVisible(not is_serial)
        if not is_serial and self._usb_device_combo.count() == 0:
            self._refresh_usb_devices()

    def _refresh_ports(self):
        ports = _list_serial_ports()
        current = self._port_combo.currentText()
        self._port_combo.clear()
        if ports:
            self._port_combo.addItems(ports)
        if current and (current in ports or not ports):
            self._port_combo.setCurrentText(current)
        elif self._port_combo.count() > 0:
            self._port_combo.setCurrentIndex(0)

    def _refresh_usb_devices(self):
        try:
            from core.app_logger import get_logger
            log = get_logger(__name__)
        except ImportError:
            log = None
        if log:
            log.debug("Rafraîchissement liste USB (bouton Rafraîchir USB)")
        try:
            from core.dos1102_usb_connection import list_usb_devices
        except ImportError as e:
            if log:
                log.debug("Import list_usb_devices: %s", e)
            QMessageBox.warning(
                self, "Oscilloscope",
                "PyUSB non disponible. Installez : pip install pyusb\n"
                "Sous Windows, installez aussi le backend libusb (ex. libusb-1.0) et le pilote WinUSB pour l'oscilloscope (Zadig).",
            )
            return
        self._usb_device_combo.clear()
        devices = list_usb_devices()
        if log:
            log.debug("Rafraîchissement USB: list_usb_devices a retourné %d périphérique(s)", len(devices))
        if not devices:
            self._usb_device_combo.addItem("Aucun périphérique USB trouvé", (None, None))
            if log:
                log.info("Aucun périphérique USB trouvé. Passez en niveau de log DEBUG (Configuration > Niveau de log) pour les détails.")
            return
        for vid, pid, desc in devices:
            self._usb_device_combo.addItem(desc, (vid, pid))
        self._usb_device_combo.setCurrentIndex(0)

    def _on_connect_clicked(self):
        if self._conn and self._conn.is_open():
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        from core.dos1102_protocol import Dos1102Protocol

        if self._conn_mode_combo.currentIndex() == 0:
            self._connect_serial(Dos1102Protocol)
        else:
            self._connect_usb(Dos1102Protocol)

    def _connect_serial(self, protocol_class):
        port = self._port_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Oscilloscope", "Choisissez un port série.")
            return
        try:
            from core.serial_connection import SerialConnection

            self._conn = SerialConnection(
                port=port,
                baudrate=self.DEFAULT_BAUD,
                timeout=2.0,
                write_timeout=2.0,
            )
            self._conn.open()
            self._protocol = protocol_class(self._conn)
            self._set_connected_status()
            self._update_connection_state(True)
        except Exception as e:
            self._cleanup_connection()
            QMessageBox.warning(self, "Oscilloscope", f"Impossible de se connecter (série) : {e}")

    def _connect_usb(self, protocol_class):
        data = self._usb_device_combo.currentData()
        if not data or data[0] is None:
            QMessageBox.warning(
                self, "Oscilloscope",
                "Choisissez un périphérique USB (bouton Rafraîchir USB si la liste est vide).",
            )
            return
        vid, pid = data
        try:
            from core.dos1102_usb_connection import Dos1102UsbConnection

            self._conn = Dos1102UsbConnection(id_vendor=vid, id_product=pid)
            self._conn.open()
            self._protocol = protocol_class(self._conn)
            self._set_connected_status()
            self._update_connection_state(True)
        except Exception as e:
            self._cleanup_connection()
            QMessageBox.warning(
                self, "Oscilloscope",
                f"Impossible de se connecter (USB) : {e}\n\n"
                "Vérifiez que le pilote WinUSB est installé pour l'oscilloscope (Zadig).",
            )

    def _set_connected_status(self):
        try:
            idn = self._protocol.idn()
            self._status_label.setText(f"Connecté — {idn[:40]}" if idn else "Connecté")
        except Exception:
            self._status_label.setText("Connecté")

    def _cleanup_connection(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._protocol = None

    def _disconnect(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._protocol = None
        self._update_connection_state(False)
        self._meas_general_label.setText("—")
        self._meas_result_label.setText("—")

    def _update_connection_state(self, connected: bool):
        self._status_indicator.set_connected(connected)
        if not connected:
            self._status_label.setText("Déconnecté")
        self._connect_btn.setText("Déconnexion" if connected else "Connexion")
        self._conn_mode_combo.setEnabled(not connected)
        self._port_combo.setEnabled(not connected)
        self._usb_device_combo.setEnabled(not connected)
        self._usb_refresh_btn.setEnabled(not connected)
        self._acq_apply_btn.setEnabled(connected)
        self._ch_apply_btn.setEnabled(connected)
        self._trig_edge_btn.setEnabled(connected)
        self._trig_video_btn.setEnabled(connected)
        self._meas_query_btn.setEnabled(connected)
        self._meas_ch_btn.setEnabled(connected)

    def _on_acq_apply(self):
        if not self._protocol:
            return
        try:
            idx = self._acq_combo.currentIndex()
            if idx == 0:
                self._protocol.set_acq_samp()
            elif idx == 1:
                self._protocol.set_acq_peak()
            else:
                self._protocol.set_acq_ave()
        except Exception as e:
            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")

    def _on_ch_apply(self):
        if not self._protocol:
            return
        try:
            c1 = self._ch1_coup_combo.currentText()
            c2 = self._ch2_coup_combo.currentText()
            self._protocol.set_ch1_coupling(c1)
            self._protocol.set_ch2_coupling(c2)
        except Exception as e:
            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")

    def _set_trigger(self, mode: str):
        if not self._protocol:
            return
        try:
            if mode == "EDGE":
                self._protocol.set_trig_edge()
            else:
                self._protocol.set_trig_video()
        except Exception as e:
            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")

    def _on_meas_general(self):
        if not self._protocol:
            return
        try:
            from core.app_logger import get_logger
            log = get_logger(__name__)
            log.debug("Mesure générale : envoi :MEAS?")
            r = self._protocol.meas()
            log.debug("Mesure générale : réponse = %r", r)
            self._meas_general_label.setText(r if r else "—")
            self._meas_result_label.setText(r if r else "—")
        except Exception as e:
            try:
                from core.app_logger import get_logger
                get_logger(__name__).exception("Mesure générale erreur: %s", e)
            except Exception:
                pass
            self._meas_result_label.setText(f"Erreur: {e}")

    def _on_meas_ch(self):
        if not self._protocol:
            return
        try:
            from core.app_logger import get_logger
            log = get_logger(__name__)
            ch = 1 if self._meas_ch_combo.currentText() == "CH1" else 2
            idx = self._meas_type_combo.currentIndex()
            meas_type = MEAS_TYPES[idx][1]
            log.debug("Mesure canal/type : CH%d %s", ch, meas_type)
            r = self._protocol.meas_ch(ch, meas_type)
            log.debug("Mesure canal/type : réponse = %r", r)
            self._meas_result_label.setText(r if r else "—")
        except Exception as e:
            try:
                from core.app_logger import get_logger
                get_logger(__name__).exception("Mesure canal/type erreur: %s", e)
            except Exception:
                pass
            self._meas_result_label.setText(f"Erreur: {e}")

    def load_config(self, config: dict) -> None:
        """Remplit le port depuis config.serial_oscilloscope."""
        osc = config.get("serial_oscilloscope") or {}
        port = (osc.get("port") or "").strip()
        if port:
            self._port_combo.setCurrentText(port)
        self._refresh_ports()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_ports()

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
