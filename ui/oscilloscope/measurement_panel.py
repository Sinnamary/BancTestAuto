"""
Panneau Mesures DOS1102 : mesure générale, mesure canal/type, toutes les mesures (Bode phase).
Réutilisable : set_protocol(), set_connected(). Utilise core.dos1102_measurements pour le formatage.
"""
from typing import Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QHeaderView,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from core import dos1102_commands as CMD
from core.dos1102_measurements import (
    format_measurements_text,
    format_meas_general_response,
    get_measure_types_per_channel,
)


class MeasGeneralWorker(QThread):
    """Thread pour exécuter :MEAS? sans bloquer l'UI."""
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, protocol: Any, parent=None):
        super().__init__(parent)
        self._protocol = protocol

    def run(self):
        try:
            r = self._protocol.meas()
            self.result_ready.emit(r if r else "")
        except Exception as e:
            self.error_occurred.emit(str(e))


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
        self._meas_general_text = QPlainTextEdit()
        self._meas_general_text.setReadOnly(True)
        self._meas_general_text.setPlaceholderText("Résultat formaté (une ligne par mesure)")
        self._meas_general_text.setMaximumHeight(140)
        self._meas_general_text.setPlainText("—")
        general_layout.addRow(QLabel("Résultat:"), self._meas_general_text)
        self._meas_query_btn = QPushButton("Mesure générale")
        self._meas_query_btn.clicked.connect(self._on_meas_general)
        self._meas_query_btn.setEnabled(False)
        general_layout.addRow("", self._meas_query_btn)
        meas_layout.addWidget(general_gb)
        self._meas_general_worker: Optional[MeasGeneralWorker] = None

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
        self._meas_general_text.setPlainText(text if text else "—")

    def _on_meas_general(self) -> None:
        if not self._protocol or self._meas_general_worker is not None and self._meas_general_worker.isRunning():
            return
        self._meas_query_btn.setEnabled(False)
        self._meas_general_text.setPlainText("En cours…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self._meas_general_worker = MeasGeneralWorker(self._protocol, self)
        self._meas_general_worker.result_ready.connect(self._on_meas_general_result)
        self._meas_general_worker.error_occurred.connect(self._on_meas_general_error)
        self._meas_general_worker.finished.connect(self._on_meas_general_finished)
        self._meas_general_worker.start()

    def _on_meas_general_result(self, raw: str) -> None:
        formatted = format_meas_general_response(raw)
        self._meas_general_text.setPlainText(formatted)
        self.set_result(formatted.split("\n")[0] if formatted else "—")
        self._show_measurement_modal(CMD.MEAS_QUERY, formatted if formatted else raw or "—")

    def _on_meas_general_error(self, message: str) -> None:
        self._meas_general_text.setPlainText(f"Erreur : {message}")
        self._show_measurement_modal(CMD.MEAS_QUERY, f"Erreur : {message}")

    def _parse_result_to_rows(self, result: str) -> list[tuple[str, str, str]]:
        """
        Découpe le résultat formaté (lignes 'Nom: valeur' ou 'Nom: valeur,OFF/ON')
        en triplets (paramètre, valeur, statut). Le suffixe ,OFF/,ON indique si la
        mesure est désactivée/activée pour ce paramètre (convention DOS1102).
        """
        rows: list[tuple[str, str, str]] = []
        for line in result.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                idx = line.index(":")
                name, rest = line[:idx].strip(), line[idx + 1 :].strip()
                # Séparer valeur et statut (ex. "15.13ms,OFF" -> valeur="15.13ms", statut="OFF")
                if rest.endswith(",OFF"):
                    value, status = rest[:-4].strip(), "OFF"
                elif rest.endswith(",ON"):
                    value, status = rest[:-3].strip(), "ON"
                else:
                    value, status = rest, "—"
                rows.append((name, value, status))
            else:
                rows.append((line, "", "—"))
        return rows

    def _show_measurement_modal(self, command: str, result: str) -> None:
        """Ouvre une fenêtre modale : commande mise en valeur et résultat en tableau."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Mesure terminée")
        dlg.setMinimumWidth(420)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        # Bloc Commande (mis en valeur)
        cmd_frame = QFrame(dlg)
        cmd_frame.setObjectName("measModalCommandFrame")
        cmd_layout = QVBoxLayout(cmd_frame)
        cmd_layout.setContentsMargins(10, 8, 10, 8)
        cmd_title = QLabel("Commande envoyée")
        cmd_title.setObjectName("measModalCommandTitle")
        cmd_layout.addWidget(cmd_title)
        cmd_label = QLabel(command)
        cmd_label.setObjectName("measModalCommandValue")
        cmd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd_layout.addWidget(cmd_label)
        layout.addWidget(cmd_frame)

        # Bloc Résultat (tableau ou texte)
        result_title = QLabel("Réponse")
        result_title.setObjectName("measModalResultTitle")
        layout.addWidget(result_title)
        rows = self._parse_result_to_rows(result)
        if rows:
            table = QTableWidget(len(rows), 3)
            table.setObjectName("measModalTable")
            table.setHorizontalHeaderLabels(["Paramètre", "Valeur", "Statut"])
            table.setColumnWidth(0, 160)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.setToolTip(
                "Statut : ON = mesure affichée à l'écran, OFF = non affichée (la valeur est quand même lue par :MEAS?)."
            )
            for i, (name, value, status) in enumerate(rows):
                table.setItem(i, 0, QTableWidgetItem(name))
                table.setItem(i, 1, QTableWidgetItem(value))
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(i, 2, status_item)
            table.setMinimumHeight(min(220, 28 * len(rows) + 28))
            layout.addWidget(table)
        else:
            result_edit = QPlainTextEdit(result)
            result_edit.setObjectName("measModalResultText")
            result_edit.setReadOnly(True)
            result_edit.setMinimumHeight(120)
            layout.addWidget(result_edit)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        bbox.accepted.connect(dlg.accept)
        layout.addWidget(bbox)

        # Style cohérent avec le thème (palette) : commande et tableau mis en valeur
        dlg.setStyleSheet("""
            QDialog {
                font-size: 13px;
            }
            #measModalCommandFrame {
                background-color: palette(midlight);
                border: 1px solid palette(mid);
                border-radius: 6px;
            }
            #measModalCommandTitle {
                font-weight: bold;
                color: palette(text);
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            #measModalCommandValue {
                font-family: Consolas, "Courier New", monospace;
                font-size: 14px;
                font-weight: 600;
                color: palette(link);
            }
            #measModalResultTitle {
                font-weight: bold;
                color: palette(text);
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            #measModalTable {
                background-color: palette(base);
                gridline-color: palette(mid);
                border: 1px solid palette(mid);
                border-radius: 4px;
            }
            #measModalTable::item {
                padding: 4px 8px;
            }
            #measModalTable::item:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
            }
            #measModalTable QHeaderView::section {
                background-color: palette(midlight);
                padding: 6px 8px;
                border: none;
                border-bottom: 2px solid palette(mid);
                font-weight: bold;
            }
            #measModalResultText {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px;
            }
        """)
        dlg.exec()

    def _on_meas_general_finished(self) -> None:
        QApplication.restoreOverrideCursor()
        self._meas_query_btn.setEnabled(True)
        self._meas_general_worker = None

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
