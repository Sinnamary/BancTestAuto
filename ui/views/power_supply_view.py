"""
Vue onglet Alimentation RS305P — tension, courant, sortie ON/OFF.
Utilise la connexion déjà établie par le bridge (Connecter tout / Charger config).
"""
from __future__ import annotations

from typing import Any, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QMessageBox,
    QFormLayout,
)


class PowerSupplyView(QWidget):
    """Onglet Alimentation RS305P. Utilise la connexion du bridge si disponible."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn: Any = None
        self._protocol: Any = None
        self._build_ui()

    def set_connection(self, conn: Optional[Any]) -> None:
        """Utilise la connexion série fournie par le bridge (ou None si déconnecté)."""
        self._conn = None
        self._protocol = None
        if conn is not None and getattr(conn, "is_open", lambda: False)():
            try:
                from core.rs305p_protocol import Rs305pProtocol
                self._conn = conn
                self._protocol = Rs305pProtocol(conn, slave_addr=1)
                self._protocol.get_output()
            except Exception:
                self._conn = None
                self._protocol = None
        self._update_connection_state(self._protocol is not None)
        if self._protocol is None:
            self._u_display_label.setText("— V")
            self._i_display_label.setText("— A")
            self._output_label.setText("OFF")

    def load_config(self, config: dict) -> None:
        """Optionnel : pas de port à charger, la connexion vient du bridge."""
        pass

    def _build_ui(self):
        layout = QVBoxLayout(self)

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

    def _update_connection_state(self, connected: bool):
        """Active ou désactive les contrôles selon la connexion bridge."""
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

    def _disconnect(self):
        """Réinitialise l'état sans fermer la connexion (gérée par le bridge)."""
        self._conn = None
        self._protocol = None
        self._update_connection_state(False)
        self._u_display_label.setText("— V")
        self._i_display_label.setText("— A")
        self._output_label.setText("OFF")
