"""
Vue onglet Alimentation RS305P — connexion série, tension, courant, sortie ON/OFF.
Connexion et déconnexion gérées dans l'onglet. Aucune dépendance config.json.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QMessageBox,
    QFormLayout,
    QFrame,
)


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


class PowerSupplyView(QWidget):
    """Onglet Alimentation RS305P. Connexion série gérée localement."""

    RS305P_BAUD = 9600

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn = None
        self._protocol = None
        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        conn_gb = QGroupBox("Connexion série")
        conn_layout = QHBoxLayout(conn_gb)
        conn_layout.addWidget(QLabel("Port:"))
        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setEditable(True)
        conn_layout.addWidget(self._port_combo)
        conn_layout.addWidget(QLabel(f"Vitesse: {self.RS305P_BAUD}"))
        self._connect_btn = QPushButton("Connexion")
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        conn_layout.addWidget(self._connect_btn)
        self._status_indicator = StatusIndicator(False, self)
        conn_layout.addWidget(self._status_indicator)
        self._status_label = QLabel("Déconnecté")
        conn_layout.addWidget(self._status_label)
        conn_layout.addStretch()
        layout.addWidget(conn_gb)

        params_gb = QGroupBox("Paramètres de sortie")
        form = QFormLayout(params_gb)
        self._voltage_spin = QDoubleSpinBox()
        self._voltage_spin.setRange(0, 30)
        self._voltage_spin.setValue(0)
        self._voltage_spin.setDecimals(2)
        self._voltage_spin.setSuffix(" V")
        form.addRow("Tension (V)", self._voltage_spin)
        self._current_spin = QDoubleSpinBox()
        self._current_spin.setRange(0, 5)
        self._current_spin.setValue(0)
        self._current_spin.setDecimals(3)
        self._current_spin.setSuffix(" A")
        form.addRow("Courant (A)", self._current_spin)
        apply_layout = QHBoxLayout()
        self._apply_btn = QPushButton("Appliquer")
        self._apply_btn.clicked.connect(self._on_apply)
        self._apply_btn.setEnabled(False)
        apply_layout.addWidget(self._apply_btn)
        apply_layout.addStretch()
        form.addRow("", apply_layout)
        layout.addWidget(params_gb)

        presets_gb = QGroupBox("Préréglages (sortie OFF, 0,5 A)")
        presets_layout = QHBoxLayout(presets_gb)
        presets_layout.addWidget(QLabel("Tension rapide :"))
        self._preset_btns = []
        for v in (3.3, 5.0, 9.0, 12.0):
            btn = QPushButton(f"{v} V")
            btn.clicked.connect(lambda checked, volt=v: self._on_preset(volt))
            btn.setEnabled(False)
            presets_layout.addWidget(btn)
            self._preset_btns.append(btn)
        presets_layout.addStretch()
        layout.addWidget(presets_gb)

        out_gb = QGroupBox("Sortie")
        out_layout = QHBoxLayout(out_gb)
        self._off_btn = QPushButton("Sortie OFF")
        self._off_btn.clicked.connect(self._on_output_off)
        self._off_btn.setEnabled(False)
        self._on_btn = QPushButton("Sortie ON")
        self._on_btn.clicked.connect(self._on_output_on)
        self._on_btn.setEnabled(False)
        out_layout.addWidget(self._off_btn)
        out_layout.addWidget(self._on_btn)
        out_layout.addWidget(QLabel("État actuel :"))
        self._output_label = QLabel("OFF")
        out_layout.addWidget(self._output_label)
        out_layout.addStretch()
        layout.addWidget(out_gb)

        read_gb = QGroupBox("Valeurs mesurées")
        read_layout = QFormLayout(read_gb)
        self._u_display_label = QLabel("— V")
        self._i_display_label = QLabel("— A")
        read_layout.addRow("Tension affichée", self._u_display_label)
        read_layout.addRow("Courant affiché", self._i_display_label)
        self._refresh_read_btn = QPushButton("Rafraîchir")
        self._refresh_read_btn.clicked.connect(self._refresh_display_values)
        self._refresh_read_btn.setEnabled(False)
        read_layout.addRow("", self._refresh_read_btn)
        layout.addWidget(read_gb)

        layout.addStretch()

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
        if self._conn and self._conn.is_open():
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self._port_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Alimentation", "Choisissez un port série.")
            return
        try:
            from core.serial_connection import SerialConnection
            from core.rs305p_protocol import Rs305pProtocol

            self._conn = SerialConnection(
                port=port,
                baudrate=self.RS305P_BAUD,
                timeout=1.0,
                write_timeout=1.0,
            )
            self._conn.open()
            self._protocol = Rs305pProtocol(self._conn, slave_addr=1)
            self._protocol.get_output()
            self._update_connection_state(True)
            self._refresh_display_values()
        except Exception as e:
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
            self._protocol = None
            QMessageBox.warning(
                self, "Alimentation",
                f"Impossible de se connecter : {e}",
            )

    def _disconnect(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._protocol = None
        self._update_connection_state(False)
        self._u_display_label.setText("— V")
        self._i_display_label.setText("— A")
        self._output_label.setText("OFF")

    def _update_connection_state(self, connected: bool):
        self._status_indicator.set_connected(connected)
        self._status_label.setText("Connecté" if connected else "Déconnecté")
        self._connect_btn.setText("Déconnexion" if connected else "Connexion")
        self._port_combo.setEnabled(not connected)
        for w in (
            self._apply_btn,
            self._off_btn,
            self._on_btn,
            self._refresh_read_btn,
            *self._preset_btns,
        ):
            w.setEnabled(connected)

    def _on_preset(self, voltage_v: float):
        """Applique un préréglage : tension, 0,5 A, sortie OFF."""
        if not self._protocol:
            return
        try:
            self._protocol.set_voltage(voltage_v)
            self._protocol.set_current(0.5)
            self._protocol.set_output(False)
            self._voltage_spin.setValue(voltage_v)
            self._current_spin.setValue(0.5)
            self._output_label.setText("OFF")
        except Exception as e:
            QMessageBox.warning(self, "Alimentation", f"Erreur : {e}")

    def _on_apply(self):
        if not self._protocol:
            return
        try:
            v = self._voltage_spin.value()
            i = self._current_spin.value()
            self._protocol.set_voltage(v)
            self._protocol.set_current(i)
        except Exception as e:
            QMessageBox.warning(self, "Alimentation", f"Erreur : {e}")

    def _on_output_on(self):
        if not self._protocol:
            return
        try:
            self._protocol.set_output(True)
            self._output_label.setText("ON")
        except Exception as e:
            QMessageBox.warning(self, "Alimentation", f"Erreur : {e}")

    def _on_output_off(self):
        if not self._protocol:
            return
        try:
            self._protocol.set_output(False)
            self._output_label.setText("OFF")
        except Exception as e:
            QMessageBox.warning(self, "Alimentation", f"Erreur : {e}")

    def _refresh_display_values(self):
        if not self._protocol:
            return
        try:
            u = self._protocol.get_voltage()
            i = self._protocol.get_current()
            on = self._protocol.get_output()
            self._u_display_label.setText(f"{u:.2f} V")
            self._i_display_label.setText(f"{i:.3f} A")
            self._output_label.setText("ON" if on else "OFF")
        except Exception as e:
            QMessageBox.warning(self, "Alimentation", f"Erreur lecture : {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_ports()

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
