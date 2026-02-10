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
        for label, _ in self._meas_types:
            self._meas_type_combo.addItem(label)
        meas_layout.addRow(self._meas_type_combo)
        btn_row = QHBoxLayout()
        self._meas_query_btn = QPushButton("Mesure générale")
        self._meas_query_btn.clicked.connect(self._on_meas_general)
        self._meas_query_btn.setEnabled(False)
        self._meas_ch_btn = QPushButton("Mesure canal/type")
        self._meas_ch_btn.clicked.connect(self._on_meas_ch)
        self._meas_ch_btn.setEnabled(False)
        btn_row.addWidget(self._meas_query_btn)
        btn_row.addWidget(self._meas_ch_btn)
        meas_layout.addRow("", btn_row)
        meas_layout.addRow(QLabel("Résultat:"))
        self._meas_result_label = QLabel("—")
        meas_layout.addRow(self._meas_result_label)
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
        self._meas_ch_btn.setEnabled(connected)
        self._meas_all_btn.setEnabled(connected)

    def set_result(self, text: str) -> None:
        self._meas_result_label.setText(text)

    def set_general_result(self, text: str) -> None:
        self._meas_general_label.setText(text)

    def _on_meas_general(self) -> None:
        if not self._protocol:
            return
        try:
            r = self._protocol.meas()
            t = r if r else "—"
            self._meas_general_label.setText(t)
            self._meas_result_label.setText(t)
        except Exception as e:
            self._meas_result_label.setText(f"Erreur: {e}")

    def _on_meas_ch(self) -> None:
        if not self._protocol:
            return
        try:
            ch = 1 if self._meas_ch_combo.currentText() == "CH1" else 2
            idx = self._meas_type_combo.currentIndex()
            meas_type = self._meas_types[idx][1]
            r = self._protocol.meas_ch(ch, meas_type)
            self._meas_result_label.setText(r if r else "—")
        except Exception as e:
            self._meas_result_label.setText(f"Erreur: {e}")

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
