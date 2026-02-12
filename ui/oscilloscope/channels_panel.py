"""
Panneau Canaux DOS1102 (CH1 / CH2) aligné sur la maquette.

Pour chaque voie : activation, couplage, échelle, position, offset, inversion,
plus une colonne de commandes (Appliquer, Auto scale, Copier CH1→CH2).
La logique réelle est pilotée via set_protocol().
"""
import time
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QSizePolicy,
    QWidget,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
)


class OscilloscopeChannelsPanel(QWidget):
    """Voies 1 et 2 : paramètres principaux (couplage, échelle, position, offset, inversion)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        gb = QGroupBox("Canaux")
        ch_layout = QHBoxLayout(gb)
        ch_layout.setSpacing(16)

        # --- Voie 1 ---
        v1 = QGroupBox("Voie 1 (CH1)")
        v1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        f1 = QFormLayout(v1)
        self._ch1_enable = QCheckBox("Activer CH1")
        self._ch1_enable.setChecked(True)
        f1.addRow("", self._ch1_enable)

        self._ch1_coup = QComboBox()
        self._ch1_coup.addItems(["DC", "AC", "GND"])
        f1.addRow(QLabel("Couplage :"), self._ch1_coup)

        self._ch1_scale = QDoubleSpinBox()
        self._ch1_scale.setSuffix(" V/div")
        self._ch1_scale.setRange(1e-3, 1000.0)
        self._ch1_scale.setValue(1.0)
        f1.addRow(QLabel("Échelle :"), self._ch1_scale)

        self._ch1_position = QDoubleSpinBox()
        self._ch1_position.setSuffix(" div")
        self._ch1_position.setRange(-10.0, 10.0)
        f1.addRow(QLabel("Position :"), self._ch1_position)

        self._ch1_offset = QSpinBox()
        self._ch1_offset.setSuffix(" mV")
        self._ch1_offset.setRange(-100000, 100000)
        f1.addRow(QLabel("Offset :"), self._ch1_offset)

        self._ch1_invert = QCheckBox("Inverser")
        f1.addRow("", self._ch1_invert)
        ch_layout.addWidget(v1)

        # --- Voie 2 ---
        v2 = QGroupBox("Voie 2 (CH2)")
        v2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        f2 = QFormLayout(v2)
        self._ch2_enable = QCheckBox("Activer CH2")
        self._ch2_enable.setChecked(True)
        f2.addRow("", self._ch2_enable)

        self._ch2_coup = QComboBox()
        self._ch2_coup.addItems(["DC", "AC", "GND"])
        f2.addRow(QLabel("Couplage :"), self._ch2_coup)

        self._ch2_scale = QDoubleSpinBox()
        self._ch2_scale.setSuffix(" V/div")
        self._ch2_scale.setRange(1e-3, 1000.0)
        self._ch2_scale.setValue(1.0)
        f2.addRow(QLabel("Échelle :"), self._ch2_scale)

        self._ch2_position = QDoubleSpinBox()
        self._ch2_position.setSuffix(" div")
        self._ch2_position.setRange(-10.0, 10.0)
        f2.addRow(QLabel("Position :"), self._ch2_position)

        self._ch2_offset = QSpinBox()
        self._ch2_offset.setSuffix(" mV")
        self._ch2_offset.setRange(-100000, 100000)
        f2.addRow(QLabel("Offset :"), self._ch2_offset)

        self._ch2_invert = QCheckBox("Inverser")
        f2.addRow("", self._ch2_invert)
        ch_layout.addWidget(v2)

        # --- Commandes globales ---
        commands = QGroupBox("Commandes")
        cmd_layout = QVBoxLayout(commands)
        cmd_layout.setAlignment(Qt.AlignmentFlag.AlignTop) if False else None  # garder l'import Qt inutile

        self._apply_btn = QPushButton("Appliquer canaux")
        self._apply_btn.clicked.connect(self._on_apply)
        self._apply_btn.setEnabled(False)
        cmd_layout.addWidget(self._apply_btn)

        self._auto_btn = QPushButton("Auto scale (maquette)")
        self._auto_btn.clicked.connect(self._on_auto_scale)
        self._auto_btn.setEnabled(False)
        cmd_layout.addWidget(self._auto_btn)

        self._copy_btn = QPushButton("Copier CH1→CH2")
        self._copy_btn.clicked.connect(self._on_copy_ch1_to_ch2)
        self._copy_btn.setEnabled(False)
        cmd_layout.addWidget(self._copy_btn)

        cmd_layout.addStretch()
        ch_layout.addWidget(commands)

        layout.addWidget(gb)

    def set_protocol(self, protocol: Optional[Any]) -> None:
        self._protocol = protocol

    def set_connected(self, connected: bool) -> None:
        self._apply_btn.setEnabled(connected)
        self._auto_btn.setEnabled(connected)
        self._copy_btn.setEnabled(connected)

    def _on_apply(self) -> None:
        if not self._protocol:
            return
        try:
            # Échelle en premier (certains DOS1102 n'appliquent l'échelle que si envoyée avant le couplage)
            if hasattr(self._protocol, "set_ch_scale"):
                self._protocol.set_ch_scale(1, self._ch1_scale.value())
                time.sleep(0.05)
                self._protocol.set_ch_scale(2, self._ch2_scale.value())
                time.sleep(0.05)
            # Couplage
            if hasattr(self._protocol, "set_ch1_coupling"):
                self._protocol.set_ch1_coupling(self._ch1_coup.currentText())
            if hasattr(self._protocol, "set_ch2_coupling"):
                self._protocol.set_ch2_coupling(self._ch2_coup.currentText())

            # Position / offset
            if hasattr(self._protocol, "set_ch_pos"):
                self._protocol.set_ch_pos(1, self._ch1_position.value())
                self._protocol.set_ch_pos(2, self._ch2_position.value())
            if hasattr(self._protocol, "set_ch_offset"):
                # Offset exprimé en mV dans l'UI -> conversion en V si nécessaire.
                self._protocol.set_ch_offset(1, self._ch1_offset.value() / 1000.0)
                self._protocol.set_ch_offset(2, self._ch2_offset.value() / 1000.0)

            # Inversion
            if hasattr(self._protocol, "set_ch_inv"):
                self._protocol.set_ch_inv(1, self._ch1_invert.isChecked())
                self._protocol.set_ch_inv(2, self._ch2_invert.isChecked())
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Oscilloscope", f"Erreur : {e}")

    def _on_auto_scale(self) -> None:
        # Fonctionnalité avancée à implémenter plus tard.
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Oscilloscope",
            "Auto scale n'est pas encore implémenté dans cette version.",
        )

    def set_scale_values(self, ch1_v_per_div: float, ch2_v_per_div: float) -> None:
        """Met à jour l'affichage des échelles (sans envoyer à l'oscilloscope). Utilisé quand le balayage change les calibres."""
        self._ch1_scale.setValue(ch1_v_per_div)
        self._ch2_scale.setValue(ch2_v_per_div)

    def set_ch_scale_display(self, ch: int, v_per_div: float) -> None:
        """Met à jour l'affichage de l'échelle d'un seul canal (sans envoyer à l'oscilloscope)."""
        if ch == 1:
            self._ch1_scale.setValue(v_per_div)
        elif ch == 2:
            self._ch2_scale.setValue(v_per_div)

    def _on_copy_ch1_to_ch2(self) -> None:
        """Recopie les paramètres de CH1 vers CH2 côté UI (sans re‑lire l'appareil)."""
        self._ch2_enable.setChecked(self._ch1_enable.isChecked())
        self._ch2_coup.setCurrentIndex(self._ch1_coup.currentIndex())
        self._ch2_scale.setValue(self._ch1_scale.value())
        self._ch2_position.setValue(self._ch1_position.value())
        self._ch2_offset.setValue(self._ch1_offset.value())
        self._ch2_invert.setChecked(self._ch1_invert.isChecked())
