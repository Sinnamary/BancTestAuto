"""
Vue onglet Terminal série : utilise les connexions de la barre (équipements connectés)
ou une connexion Série (COM) / USB dédiée. Envoi et réception avec CR/LF en fin de chaîne.

Phase 4 : mode "Équipement (barre)" — sélecteur listant uniquement les équipements déjà
connectés ; envoi/réception sur la connexion série de l'équipement choisi (pas de connexion propre).
"""
from typing import Callable, List, Tuple, Any, Optional

from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor

from core.app_logger import get_logger

logger = get_logger(__name__)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)


def _list_serial_ports():
    try:
        import serial.tools.list_ports
        return [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        return []


# Débits courants (config limits ou défaut)
DEFAULT_BAUDRATES = [9600, 19200, 38400, 57600, 115200]


class _UsbReadThread(QThread):
    """Thread qui lit les données USB et les émet vers le thread principal."""
    data_received = pyqtSignal(bytes)

    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self._conn = connection
        self._running = True

    def run(self):
        logger.debug("Terminal USB: thread de lecture démarré (read size=1024, timeout côté connexion)")
        loop_count = 0
        while self._running and self._conn and self._conn.is_open():
            loop_count += 1
            if loop_count <= 3 or loop_count % 20 == 0:
                logger.debug("Terminal USB: boucle read #%d (running=%s, is_open=%s)", loop_count, self._running, self._conn.is_open() if self._conn else False)
            try:
                data = self._conn.read(1024)
                if data:
                    logger.debug("Terminal USB: reçu %d octets: %r", len(data), data[:200] if len(data) > 200 else data)
                    self.data_received.emit(data)
                else:
                    if loop_count <= 5 or loop_count % 50 == 0:
                        logger.debug("Terminal USB: read() a retourné 0 octet (boucle #%d)", loop_count)
            except Exception as e:
                logger.debug("Terminal USB: exception dans thread read: %s", e, exc_info=True)
                break
        logger.debug("Terminal USB: thread de lecture terminé (boucles=%d)", loop_count)

    def stop(self):
        self._running = False


class SerialTerminalView(QWidget):
    """Onglet Terminal série : équipement (barre), Série (COM) ou USB ; envoi avec option CR/LF, réception en temps réel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None
        self._usb_conn = None
        self._usb_thread = None
        self._preferred_usb = None  # (vid, pid) depuis config
        self._connection_provider: Optional[Callable[[], List[Tuple[Any, str, Any]]]] = None  # () -> [(kind, display_name, conn)]
        self._equipment_list: List[Tuple[Any, str, Any]] = []  # liste courante (kind, display_name, conn)
        self._equipment_conn: Any = None  # connexion série de l'équipement sélectionné (mode barre)
        self._read_timer = QTimer(self)
        self._read_timer.timeout.connect(self._poll_serial)
        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Connexion : Équipement (barre) / Série (COM) / USB ---
        conn_gb = QGroupBox("Connexion")
        conn_layout = QHBoxLayout(conn_gb)
        conn_layout.addWidget(QLabel("Mode:"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Équipement (barre)", "Série (COM)", "USB (périphérique)"])
        self._mode_combo.currentIndexChanged.connect(self._on_connection_mode_changed)
        conn_layout.addWidget(self._mode_combo)

        conn_layout.addWidget(QLabel("Équipement:"))
        self._equipment_combo = QComboBox()
        self._equipment_combo.setMinimumWidth(140)
        self._equipment_combo.setPlaceholderText("Aucun équipement connecté")
        self._equipment_combo.currentIndexChanged.connect(self._on_equipment_selection_changed)
        conn_layout.addWidget(self._equipment_combo)
        self._equipment_refresh_btn = QPushButton("Actualiser")
        self._equipment_refresh_btn.clicked.connect(self._refresh_equipment_list)
        conn_layout.addWidget(self._equipment_refresh_btn)

        conn_layout.addWidget(QLabel("Port:"))
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setEditable(True)
        conn_layout.addWidget(self._port_combo)
        self._refresh_ports_btn = QPushButton("Actualiser")
        self._refresh_ports_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(self._refresh_ports_btn)
        conn_layout.addWidget(QLabel("Débit:"))
        self._baud_combo = QComboBox()
        self._baud_combo.setMinimumWidth(90)
        for b in DEFAULT_BAUDRATES:
            self._baud_combo.addItem(str(b))
        self._baud_combo.setCurrentText("115200")
        conn_layout.addWidget(self._baud_combo)

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
        self._status_label = QLabel("Déconnecté")
        conn_layout.addWidget(self._status_label)
        conn_layout.addStretch()
        layout.addWidget(conn_gb)
        self._on_connection_mode_changed()

        # --- Options d'envoi : CR / LF en fin de chaîne ---
        send_opts_gb = QGroupBox("Envoi : fin de chaîne")
        send_opts_layout = QHBoxLayout(send_opts_gb)
        self._check_cr = QCheckBox("Ajouter CR (\\r) en fin de chaîne")
        self._check_cr.setChecked(False)
        send_opts_layout.addWidget(self._check_cr)
        self._check_lf = QCheckBox("Ajouter LF (\\n) en fin de chaîne")
        self._check_lf.setChecked(True)
        send_opts_layout.addWidget(self._check_lf)
        send_opts_layout.addStretch()
        layout.addWidget(send_opts_gb)

        # --- Envoi ---
        send_gb = QGroupBox("Envoyer")
        send_layout = QHBoxLayout(send_gb)
        self._command_edit = QLineEdit()
        self._command_edit.setPlaceholderText("Commande à envoyer...")
        self._command_edit.returnPressed.connect(self._send_command)
        send_layout.addWidget(self._command_edit)
        self._send_btn = QPushButton("Envoyer")
        self._send_btn.clicked.connect(self._send_command)
        self._send_btn.setEnabled(False)
        send_layout.addWidget(self._send_btn)
        self._clear_cmd_btn = QPushButton("Effacer")
        self._clear_cmd_btn.clicked.connect(self._command_edit.clear)
        self._clear_cmd_btn.setToolTip("Efface la ligne à envoyer")
        send_layout.addWidget(self._clear_cmd_btn)
        layout.addWidget(send_gb)

        # --- Réception ---
        recv_gb = QGroupBox("Réception")
        recv_layout = QVBoxLayout(recv_gb)
        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText("Données reçues...")
        recv_layout.addWidget(self._output_text)
        clear_btn = QPushButton("Vider")
        clear_btn.clicked.connect(self._output_text.clear)
        recv_layout.addWidget(clear_btn)
        layout.addWidget(recv_gb)

    def _on_connection_mode_changed(self):
        mode = self._mode_combo.currentIndex()
        is_equipment = mode == 0
        is_serial = mode == 1
        is_usb = mode == 2
        self._equipment_combo.setVisible(is_equipment)
        self._equipment_refresh_btn.setVisible(is_equipment)
        self._port_combo.setVisible(is_serial)
        self._refresh_ports_btn.setVisible(is_serial)
        self._baud_combo.setVisible(is_serial)
        self._usb_combo.setVisible(is_usb)
        self._usb_refresh_btn.setVisible(is_usb)
        self._connect_btn.setVisible(not is_equipment)
        if is_equipment:
            self._refresh_equipment_list()
            self._update_equipment_status_label()
        elif is_usb and self._usb_combo.count() == 0:
            self._refresh_usb()
        elif is_usb:
            self._apply_preferred_usb()
        else:
            self._status_label.setText("Déconnecté" if not self._is_connected() else self._status_label.text())

    def set_connection_provider(self, provider: Optional[Callable[[], List[Tuple[Any, str, Any]]]]) -> None:
        """Injecte le fournisseur de liste d'équipements connectés (kind, display_name, conn). Phase 4."""
        self._connection_provider = provider
        self._refresh_equipment_list()

    def _refresh_equipment_list(self) -> None:
        """Met à jour la liste des équipements connectés (mode Équipement barre)."""
        self._equipment_list = []
        if self._connection_provider:
            try:
                self._equipment_list = self._connection_provider()
            except Exception as e:
                logger.debug("Terminal: refresh equipment list failed: %s", e)
        self._equipment_combo.clear()
        for _kind, display_name, _conn in self._equipment_list:
            self._equipment_combo.addItem(display_name)
        if self._equipment_combo.count() > 0 and self._equipment_conn is None:
            self._equipment_combo.setCurrentIndex(0)
        elif self._equipment_combo.count() == 0:
            self._equipment_conn = None
        self._on_equipment_selection_changed()

    def _on_equipment_selection_changed(self) -> None:
        idx = self._equipment_combo.currentIndex()
        if 0 <= idx < len(self._equipment_list):
            _kind, _name, conn = self._equipment_list[idx]
            self._equipment_conn = conn if (conn and getattr(conn, "is_open", lambda: False)()) else None
        else:
            self._equipment_conn = None
        if self._mode_combo.currentIndex() == 0:
            self._update_equipment_status_label()
            self._send_btn.setEnabled(self._equipment_conn is not None)
            if self._equipment_conn:
                if not self._read_timer.isActive():
                    self._read_timer.start(50)
            else:
                self._read_timer.stop()

    def _update_equipment_status_label(self) -> None:
        if self._equipment_conn:
            idx = self._equipment_combo.currentIndex()
            name = self._equipment_combo.currentText() if 0 <= idx < self._equipment_combo.count() else "Équipement"
            self._status_label.setText(f"Équipement : {name}")
        else:
            self._status_label.setText("Aucun équipement sélectionné" if self._equipment_combo.count() == 0 else "Sélectionnez un équipement")

    def _refresh_ports(self):
        ports = _list_serial_ports()
        current = self._port_combo.currentText()
        self._port_combo.clear()
        if ports:
            self._port_combo.addItems(ports)
        if current and current in ports:
            self._port_combo.setCurrentText(current)
        elif self._port_combo.count() > 0:
            self._port_combo.setCurrentIndex(0)

    def _refresh_usb(self):
        try:
            from core.dos1102_usb_connection import list_usb_devices
        except ImportError:
            QMessageBox.warning(
                self, "Terminal série",
                "PyUSB non disponible. Installez : pip install pyusb\n"
                "Sous Windows, installez aussi le backend libusb et le pilote WinUSB (Zadig).",
            )
            return
        self._usb_combo.clear()
        devices = list_usb_devices()
        if not devices:
            self._usb_combo.addItem("Aucun périphérique USB trouvé", (None, None))
        else:
            for vid, pid, desc in devices:
                self._usb_combo.addItem(desc, (vid, pid))
            self._usb_combo.setCurrentIndex(0)
        self._apply_preferred_usb()

    def _apply_preferred_usb(self):
        if not self._preferred_usb:
            return
        vid_pref, pid_pref = self._preferred_usb
        for idx in range(self._usb_combo.count()):
            data = self._usb_combo.itemData(idx)
            if not data or data[0] is None:
                continue
            if data[0] == vid_pref and data[1] == pid_pref:
                self._usb_combo.setCurrentIndex(idx)
                break

    def _on_connect_clicked(self):
        if self._is_connected():
            self._disconnect()
        else:
            self._connect()

    def _is_connected(self):
        if self._mode_combo.currentIndex() == 0:
            return self._equipment_conn is not None and getattr(self._equipment_conn, "is_open", lambda: False)()
        if self._serial and self._serial.is_open:
            return True
        if self._usb_conn and self._usb_conn.is_open():
            return True
        return False

    def _connect(self):
        if self._mode_combo.currentIndex() == 0:
            self._connect_serial()
        else:
            self._connect_usb()

    def _connect_serial(self):
        port = self._port_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Terminal série", "Choisissez un port série.")
            return
        try:
            baud = int(self._baud_combo.currentText())
        except ValueError:
            QMessageBox.warning(self, "Terminal série", "Débit invalide.")
            return
        try:
            import serial
            self._serial = serial.Serial(
                port=port,
                baudrate=baud,
                timeout=0.05,
                write_timeout=2.0,
            )
            self._read_timer.start(50)
            self._update_connection_state(True, port=port, baud=baud)
            self._append_received(f"[Connecté sur {port} @ {baud} bauds]\n")
        except Exception as e:
            if self._serial:
                try:
                    self._serial.close()
                except Exception:
                    pass
                self._serial = None
            msg = str(e).strip()
            if "already open" in msg.lower() or "déjà ouvert" in msg.lower():
                detail = (
                    f"Connexion à {port} @ {baud} bauds : ce port est déjà utilisé.\n\n"
                    "Fermez tout logiciel qui utilise ce port, ou essayez un autre port (ex. COM3, COM4)."
                )
            else:
                detail = f"Impossible de se connecter sur {port} @ {baud} bauds : {e}"
            QMessageBox.warning(self, "Terminal série", detail)

    def _connect_usb(self):
        data = self._usb_combo.currentData()
        if not data or data[0] is None:
            logger.debug("Terminal USB: connexion refusée — aucun périphérique sélectionné")
            QMessageBox.warning(
                self, "Terminal série",
                "Choisissez un périphérique USB (Rafraîchir USB si vide).",
            )
            return
        vid, pid = data
        logger.debug("Terminal USB: tentative connexion VID=0x%04x PID=0x%04x", vid, pid)
        try:
            from core.dos1102_usb_connection import Dos1102UsbConnection
        except ImportError as e:
            logger.debug("Terminal USB: ImportError Dos1102UsbConnection: %s", e)
            QMessageBox.warning(
                self, "Terminal série",
                "PyUSB non disponible. Installez : pip install pyusb",
            )
            return
        try:
            # Timeout de lecture court pour le terminal (réactivité)
            self._usb_conn = Dos1102UsbConnection(
                vid, pid,
                read_timeout_ms=500,
                write_timeout_ms=2000,
            )
            logger.debug("Terminal USB: ouverture connexion (read_timeout_ms=500, write_timeout_ms=2000)")
            self._usb_conn.open()
            # Vider les données en attente d'une session précédente (évite d'afficher une vieille réponse au redémarrage)
            flushed = self._usb_conn.flush_input(timeout_ms=50, max_reads=50)
            if flushed:
                logger.debug("Terminal USB: %d octets de tampon vidés avant démarrage lecture", flushed)
            logger.debug("Terminal USB: connexion ouverte, démarrage thread de lecture")
            self._usb_thread = _UsbReadThread(self._usb_conn, self)
            self._usb_thread.data_received.connect(self._on_usb_data_received)
            self._usb_thread.start()
            desc = self._usb_combo.currentText()
            self._update_connection_state(True, usb_desc=desc)
            self._append_received(f"[Connecté USB : {desc}]\n")
            logger.debug("Terminal USB: connecté — %s", desc)
        except Exception as e:
            logger.debug("Terminal USB: échec connexion: %s", e, exc_info=True)
            if self._usb_conn:
                try:
                    self._usb_conn.close()
                except Exception:
                    pass
                self._usb_conn = None
            QMessageBox.warning(
                self, "Terminal série",
                f"Impossible de se connecter au périphérique USB : {e}\n\n"
                "Vérifiez le pilote WinUSB (Zadig).",
            )

    def _on_usb_data_received(self, data: bytes):
        logger.debug("Terminal USB: _on_usb_data_received(%d octets) -> affichage", len(data))
        try:
            text = data.decode("utf-8", errors="replace")
            logger.debug("Terminal USB: décodé UTF-8: %r", text[:300] if len(text) > 300 else text)
        except Exception as e:
            text = data.hex(" ")
            logger.debug("Terminal USB: décodage UTF-8 échoué (%s), affichage hex: %s", e, text[:100])
        self._append_received(text)

    def _disconnect(self):
        self._read_timer.stop()
        # Fermer d'abord la connexion USB pour que le thread de lecture se débloque
        if self._usb_conn:
            logger.debug("Terminal USB: déconnexion — fermeture connexion USB")
            try:
                self._usb_conn.close()
            except Exception as e:
                logger.debug("Terminal USB: close() a levé: %s", e)
            self._usb_conn = None
        if self._usb_thread:
            logger.debug("Terminal USB: arrêt thread de lecture, wait(2000)")
            self._usb_thread.stop()
            self._usb_thread.wait(2000)
            self._usb_thread = None
            logger.debug("Terminal USB: thread arrêté")
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        self._update_connection_state(False)
        self._append_received("[Déconnecté]\n")

    def _update_connection_state(self, connected: bool, port: str = "", baud: int = 0, usb_desc: str = ""):
        if connected and usb_desc:
            self._status_label.setText(f"Connecté USB — {usb_desc}")
        elif connected and port and baud:
            self._status_label.setText(f"Connecté ({port} @ {baud} bauds)")
        else:
            self._status_label.setText("Connecté" if connected else "Déconnecté")
        self._connect_btn.setText("Déconnexion" if connected else "Connexion")
        self._mode_combo.setEnabled(not connected)
        self._port_combo.setEnabled(not connected)
        self._refresh_ports_btn.setEnabled(not connected)
        self._baud_combo.setEnabled(not connected)
        self._usb_combo.setEnabled(not connected)
        self._usb_refresh_btn.setEnabled(not connected)
        self._send_btn.setEnabled(connected)

    def _get_current_connection(self):
        """Retourne (connection, is_usb) pour envoi/réception, ou (None, False) si non connecté."""
        if self._mode_combo.currentIndex() == 0 and self._equipment_conn and getattr(self._equipment_conn, "is_open", lambda: False)():
            return self._equipment_conn, False
        if self._serial and self._serial.is_open:
            return self._serial, False
        if self._usb_conn and self._usb_conn.is_open():
            return self._usb_conn, True
        return None, False

    def _send_command(self):
        conn, is_usb = self._get_current_connection()
        if conn is None:
            logger.debug("Terminal: _send_command ignoré (non connecté)")
            return
        text = self._command_edit.text()
        data = text.encode("utf-8", errors="replace")
        if self._check_cr.isChecked():
            data += b"\r"
        if self._check_lf.isChecked():
            data += b"\n"
        if not data:
            return
        if is_usb:
            logger.debug("Terminal USB: envoi %d octets: %r", len(data), data)
        try:
            conn.write(data)
            self._append_received(f"> {text}\n")
            if is_usb:
                logger.debug("Terminal USB: write() OK")
        except Exception as e:
            logger.debug("Terminal: write() erreur: %s", e, exc_info=True)
            QMessageBox.warning(self, "Terminal série", f"Erreur envoi : {e}")

    def _poll_serial(self):
        # Mode Équipement (barre) : connexion série partagée (SerialConnection avec in_waiting/read)
        if self._mode_combo.currentIndex() == 0 and self._equipment_conn:
            try:
                if not getattr(self._equipment_conn, "is_open", lambda: False)():
                    return
                n = getattr(self._equipment_conn, "in_waiting", lambda: 0)()
                if n > 0:
                    data = self._equipment_conn.read(min(n, 1024))
                    if data:
                        try:
                            text = data.decode("utf-8", errors="replace")
                        except Exception:
                            text = data.hex(" ")
                        self._append_received(text)
            except Exception:
                pass
            return
        # Mode Série (COM)
        if not self._serial or not self._serial.is_open:
            return
        try:
            n = self._serial.in_waiting
            if n > 0:
                data = self._serial.read(n)
                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = data.hex(" ")
                self._append_received(text)
        except Exception:
            pass

    def _append_received(self, text: str):
        self._output_text.moveCursor(QTextCursor.MoveOperation.End)
        self._output_text.insertPlainText(text)
        self._output_text.moveCursor(QTextCursor.MoveOperation.End)

    def load_config(self, config: dict):
        """Applique options de débit (limits.baudrate_options) et périphérique USB préféré (usb_oscilloscope)."""
        opts = (config.get("limits") or {}).get("baudrate_options", DEFAULT_BAUDRATES)
        if opts and self._baud_combo.count() != len(opts):
            current = self._baud_combo.currentText()
            self._baud_combo.clear()
            for b in opts:
                self._baud_combo.addItem(str(b))
            try:
                if current and int(current) in opts:
                    self._baud_combo.setCurrentText(current)
            except ValueError:
                pass
        usb_cfg = config.get("usb_oscilloscope") or {}
        vid = usb_cfg.get("vendor_id")
        pid = usb_cfg.get("product_id")
        if isinstance(vid, int) and isinstance(pid, int):
            self._preferred_usb = (vid, pid)
            self._apply_preferred_usb()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_ports()
        if self._mode_combo.currentIndex() == 0:
            self._refresh_equipment_list()

    def disconnect_serial(self):
        """Déconnexion propre (appelée par la fenêtre principale à la fermeture)."""
        self._disconnect()

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
