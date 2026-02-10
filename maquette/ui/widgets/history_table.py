"""
Tableau d'historique pour la maquette Multimètre.
Aligné sur `ui.widgets.history_table.HistoryTable`.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal


class HistoryTable(QWidget):
    """
    Tableau historique (#, Valeur, Unité) + Effacer / Exporter CSV.
    La maquette alimente ce widget avec set_rows().
    """

    clear_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        hist_gb = QGroupBox("Historique")
        hist_layout = QVBoxLayout(hist_gb)
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["#", "Valeur", "Unité"])
        hist_layout.addWidget(self._table)
        btn_row = QHBoxLayout()
        self._export_btn = QPushButton("Exporter CSV")
        self._clear_btn = QPushButton("Effacer")
        self._export_btn.clicked.connect(self.export_requested.emit)
        self._clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self._export_btn)
        btn_row.addWidget(self._clear_btn)
        hist_layout.addLayout(btn_row)
        layout.addWidget(hist_gb)

    def _on_clear(self):
        self.clear()
        self.clear_requested.emit()

    def set_rows(self, rows: list) -> None:
        """
        Affiche les lignes. rows = liste de (value_str, unit).
        """
        self._table.setRowCount(len(rows))
        for i, (val, unit) in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._table.setItem(i, 1, QTableWidgetItem(val))
            self._table.setItem(i, 2, QTableWidgetItem(unit))

    def clear(self) -> None:
        """Vide le tableau (n'émet pas clear_requested)."""
        self._table.setRowCount(0)

