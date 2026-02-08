"""
Vue onglet Terminal série : connexion sur un port série valide, envoi et réception
de commandes avec cases à cocher CR/LF en fin de chaîne à l'envoi.
"""
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor
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


class SerialTerminalView(QWidget):
    """Onglet Terminal série : connexion, envoi avec option CR/LF, réception en temps réel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None
        self._read_timer = QTimer(self)
        self._read_timer.timeout.connect(self._poll_serial)
        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Connexion ---
        conn_gb = QGroupBox("Connexion série")
        conn_layout = QHBoxLayout(conn_gb)
        conn_layout.addWidget(QLabel("Port:"))
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setEditable(True)
        conn_layout.addWidget(self._port_combo)
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(refresh_btn)
        conn_layout.addWidget(QLabel("Débit:"))
        self._baud_combo = QComboBox()
        self._baud_combo.setMinimumWidth(90)
        for b in DEFAULT_BAUDRATES:
            self._baud_combo.addItem(str(b))
        self._baud_combo.setCurrentText("115200")
        conn_layout.addWidget(self._baud_combo)
        self._connect_btn = QPushButton("Connexion")
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        conn_layout.addWidget(self._connect_btn)
        self._status_label = QLabel("Déconnecté")
        conn_layout.addWidget(self._status_label)
        conn_layout.addStretch()
        layout.addWidget(conn_gb)

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

    def _on_connect_clicked(self):
        if self._serial and self._serial.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
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
            self._serial.open()
            self._read_timer.start(50)
            self._update_connection_state(True)
            self._append_received("[Connecté]\n")
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
                    "Ce port est déjà utilisé.\n\n"
                    "• Soit par le Multimètre ou le Générateur dans cette application "
                    "(voir Paramètres / config).\n"
                    "• Soit par un autre programme (autre logiciel, autre instance).\n\n"
                    "Choisissez un autre port (ex. COM3, COM4) ou fermez l’utilisation actuelle du port."
                )
            else:
                detail = f"Impossible de se connecter : {e}"
            QMessageBox.warning(self, "Terminal série", detail)

    def _disconnect(self):
        self._read_timer.stop()
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None
        self._update_connection_state(False)
        self._append_received("[Déconnecté]\n")

    def _update_connection_state(self, connected: bool):
        self._status_label.setText("Connecté" if connected else "Déconnecté")
        self._connect_btn.setText("Déconnexion" if connected else "Connexion")
        self._port_combo.setEnabled(not connected)
        self._baud_combo.setEnabled(not connected)
        self._send_btn.setEnabled(connected)

    def _send_command(self):
        if not self._serial or not self._serial.is_open:
            return
        text = self._command_edit.text()
        data = text.encode("utf-8", errors="replace")
        if self._check_cr.isChecked():
            data += b"\r"
        if self._check_lf.isChecked():
            data += b"\n"
        if not data:
            return
        try:
            self._serial.write(data)
            self._append_received(f"> {text}\n")
            self._command_edit.clear()
        except Exception as e:
            QMessageBox.warning(self, "Terminal série", f"Erreur envoi : {e}")

    def _poll_serial(self):
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
        """Optionnel : appliquer les options de débit depuis config (limits.baudrate_options)."""
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

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_ports()

    def disconnect_serial(self):
        """Déconnexion propre (appelée par la fenêtre principale à la fermeture)."""
        self._disconnect()

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
