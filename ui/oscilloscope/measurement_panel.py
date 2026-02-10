"""
Panneau Mesures DOS1102 : mesure générale, mesure canal/type, toutes les mesures (Bode phase).
Réutilisable : set_protocol(), set_connected(). Utilise core.dos1102_measurements pour le formatage.
"""
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QPlainTextEdit,
    QWidget,
)

from core import dos1102_commands as CMD
from core.dos1102_measurements import format_measurements_text, get_measure_types_per_channel


class OscilloscopeMeasurementPanel(QWidget):
    """Mesure générale, mesure par canal/type, et lecture de toutes les mesures (Bode phase)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._protocol: Any = None
        self._meas_types = get_measure_types_per_channel()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        meas_gb = QGroupBox("Mesures")
        meas_layout = QVBoxLayout(meas_gb)

        # Mesures par voie : organisation similaire aux canaux (CH1 / CH2 côte à côte)
        per_channel_row = QHBoxLayout()
        per_channel_row.setSpacing(16)

        def _add_measure_types(combo: QComboBox) -> None:
            for label, _ in self._meas_types:
                combo.addItem(label)

        # Voie 1
        ch1_gb = QGroupBox("Voie 1 (CH1)")
        ch1_layout = QFormLayout(ch1_gb)
        self._meas_ch1_type_combo = QComboBox()
        _add_measure_types(self._meas_ch1_type_combo)
        ch1_layout.addRow(QLabel("Type de mesure:"), self._meas_ch1_type_combo)
        self._meas_ch1_btn = QPushButton("Mesure CH1")
        self._meas_ch1_btn.clicked.connect(self._on_meas_ch1)
        self._meas_ch1_btn.setEnabled(False)
        ch1_layout.addRow("", self._meas_ch1_btn)
        self._meas_ch1_result = QLabel("—")
        ch1_layout.addRow(QLabel("Résultat:"), self._meas_ch1_result)
        per_channel_row.addWidget(ch1_gb)

        # Voie 2
        ch2_gb = QGroupBox("Voie 2 (CH2)")
        ch2_layout = QFormLayout(ch2_gb)
        self._meas_ch2_type_combo = QComboBox()
        _add_measure_types(self._meas_ch2_type_combo)
        ch2_layout.addRow(QLabel("Type de mesure:"), self._meas_ch2_type_combo)
        self._meas_ch2_btn = QPushButton("Mesure CH2")
        self._meas_ch2_btn.clicked.connect(self._on_meas_ch2)
        self._meas_ch2_btn.setEnabled(False)
        ch2_layout.addRow("", self._meas_ch2_btn)
        self._meas_ch2_result = QLabel("—")
        ch2_layout.addRow(QLabel("Résultat:"), self._meas_ch2_result)
        per_channel_row.addWidget(ch2_gb)

        meas_layout.addLayout(per_channel_row)

        # Mesure générale (MEAS?)
        general_gb = QGroupBox("Mesure générale (:MEAS?)")
        general_layout = QFormLayout(general_gb)
        self._meas_general_label = QLabel("—")
        general_layout.addRow(QLabel("Résultat:"), self._meas_general_label)
        self._meas_query_btn = QPushButton("Mesure générale")
        self._meas_query_btn.clicked.connect(self._on_meas_general)
        self._meas_query_btn.setEnabled(False)
        general_layout.addRow("", self._meas_query_btn)
        meas_layout.addWidget(general_gb)

        layout.addWidget(meas_gb)

        meas_all_gb = QGroupBox("Toutes les mesures (Bode phase)")
        meas_all_layout = QVBoxLayout(meas_all_gb)
        row = QHBoxLayout()
        row.addWidget(QLabel("Source:"))
        self._meas_all_combo = QComboBox()
        self._meas_all_combo.addItems(["Voie 1 (CH1)", "Voie 2 (CH2)", "Inter-canal (CH2 vs CH1)"])
        row.addWidget(self._meas_all_combo)
        self._meas_all_btn = QPushButton("Lire toutes les mesures")
        self._meas_all_btn.clicked.connect(self._on_meas_all)
        self._meas_all_btn.setEnabled(False)
        row.addWidget(self._meas_all_btn)
        row.addStretch()
        meas_all_layout.addLayout(row)
        self._meas_all_text = QPlainTextEdit()
        self._meas_all_text.setPlaceholderText(
            "Résultats (libellé : valeur) — Bode phase : φ (°) = (délai / période) × 360"
        )
        self._meas_all_text.setMaximumHeight(180)
        self._meas_all_text.setReadOnly(True)
        meas_all_layout.addWidget(self._meas_all_text)
        layout.addWidget(meas_all_gb)

    def set_protocol(self, protocol: Optional[Any]) -> None:
        self._protocol = protocol

    def set_connected(self, connected: bool) -> None:
        self._meas_query_btn.setEnabled(connected)
        self._meas_ch1_btn.setEnabled(connected)
        self._meas_ch2_btn.setEnabled(connected)
        self._meas_all_btn.setEnabled(connected)

    def set_result(self, text: str) -> None:
        # Pour compatibilité avec l'ancienne interface, on met le résultat
        # sur les deux voies.
        self._meas_ch1_result.setText(text)
        self._meas_ch2_result.setText(text)

    def set_general_result(self, text: str) -> None:
        self._meas_general_label.setText(text)

    def _on_meas_general(self) -> None:
        if not self._protocol:
            return
        try:
            r = self._protocol.meas()
            t = r if r else "—"
            self._meas_general_label.setText(t)
            # On reflète aussi sur les résultats de voie pour cohérence visuelle.
            self.set_result(t)
        except Exception as e:
            self._meas_result_label.setText(f"Erreur: {e}")

    def _on_meas_ch1(self) -> None:
        self._measure_channel(1, self._meas_ch1_type_combo, self._meas_ch1_result)

    def _on_meas_ch2(self) -> None:
        self._measure_channel(2, self._meas_ch2_type_combo, self._meas_ch2_result)

    def _measure_channel(self, ch: int, combo: QComboBox, label: QLabel) -> None:
        if not self._protocol:
            return
        try:
            idx = combo.currentIndex()
            meas_type = self._meas_types[idx][1]
            r = self._protocol.meas_ch(ch, meas_type)
            label.setText(r if r else "—")
        except Exception as e:
            label.setText(f"Erreur: {e}")

    def _on_meas_all(self) -> None:
        if not self._protocol:
            return
        idx = self._meas_all_combo.currentIndex()
        try:
            if idx == 0:
                d = self._protocol.meas_all_per_channel(1)
                self._meas_all_text.setPlainText(format_measurements_text(d))
            elif idx == 1:
                d = self._protocol.meas_all_per_channel(2)
                self._meas_all_text.setPlainText(format_measurements_text(d))
            else:
                d = self._protocol.meas_all_inter_channel()
                self._meas_all_text.setPlainText(format_measurements_text(d, add_bode_hint=True))
        except Exception as e:
            self._meas_all_text.setPlainText(f"Erreur : {e}")
