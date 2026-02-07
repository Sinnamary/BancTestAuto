"""
Vue onglet Multimètre — maquette avec données factices.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
)
from PyQt6.QtCore import Qt


class MeterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        layout = QVBoxLayout(content)

        # --- Modes de mesure ---
        modes_gb = QGroupBox("Modes de mesure")
        modes_layout = QHBoxLayout(modes_gb)
        self._mode_group = QButtonGroup(self)
        modes = ["V⎓", "V~", "A⎓", "A~", "Ω", "Ω 4W", "Hz", "s", "F", "°C", "⊿", "⚡"]
        for m in modes:
            btn = QPushButton(m)
            btn.setCheckable(True)
            self._mode_group.addButton(btn)
            modes_layout.addWidget(btn)
        self._mode_group.buttons()[0].setChecked(True)
        layout.addWidget(modes_gb)

        # --- Affichage principal + secondaire ---
        display_gb = QGroupBox("Affichage")
        display_layout = QHBoxLayout(display_gb)
        self._value_label = QLabel("12.345 V")
        self._value_label.setStyleSheet("font-size: 28px; font-family: Consolas, monospace;")
        self._value_label.setMinimumWidth(200)
        display_layout.addWidget(self._value_label)
        display_layout.addStretch()
        self._secondary_check = QCheckBox("Afficher Hz")
        display_layout.addWidget(self._secondary_check)
        self._secondary_label = QLabel("1.234 kHz")
        self._secondary_label.setStyleSheet("font-size: 14px;")
        display_layout.addWidget(self._secondary_label)
        layout.addWidget(display_gb)

        # --- Plage + Vitesse + Math ---
        row = QWidget()
        row_layout = QHBoxLayout(row)
        # Plage
        range_gb = QGroupBox("Plage")
        range_layout = QVBoxLayout(range_gb)
        range_layout.addWidget(QRadioButton("Auto"))
        range_layout.addWidget(QRadioButton("Manuel"))
        range_layout.addWidget(QComboBox())  # liste plages
        row_layout.addWidget(range_gb)
        # Vitesse
        rate_gb = QGroupBox("Vitesse")
        rate_layout = QVBoxLayout(rate_gb)
        rate_layout.addWidget(QRadioButton("Rapide"))
        rate_layout.addWidget(QRadioButton("Moyenne"))
        rate_layout.addWidget(QRadioButton("Lente"))
        row_layout.addWidget(rate_gb)
        # Math
        math_gb = QGroupBox("Fonctions math")
        math_layout = QVBoxLayout(math_gb)
        math_layout.addWidget(QRadioButton("Aucun"))
        math_layout.addWidget(QRadioButton("Rel"))
        math_layout.addWidget(QRadioButton("dB"))
        math_layout.addWidget(QRadioButton("dBm"))
        math_layout.addWidget(QRadioButton("Moyenne"))
        row_layout.addWidget(math_gb)
        layout.addWidget(row)

        # --- Historique ---
        hist_gb = QGroupBox("Historique")
        hist_layout = QVBoxLayout(hist_gb)
        self._history_table = QTableWidget(5, 3)
        self._history_table.setHorizontalHeaderLabels(["#", "Valeur", "Unité"])
        for i in range(3):
            self._history_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._history_table.setItem(i, 1, QTableWidgetItem("12.34" + str(i)))
            self._history_table.setItem(i, 2, QTableWidgetItem("V"))
        hist_layout.addWidget(self._history_table)
        btn_row = QHBoxLayout()
        btn_row.addWidget(QPushButton("Exporter CSV"))
        btn_row.addWidget(QPushButton("Effacer"))
        hist_layout.addLayout(btn_row)
        layout.addWidget(hist_gb)

        # --- Actions ---
        actions = QHBoxLayout()
        actions.addWidget(QPushButton("Mesure"))
        actions.addWidget(QPushButton("Mesure continue"))
        actions.addWidget(QPushButton("Reset (*RST)"))
        actions.addWidget(QPushButton("Exporter CSV"))
        layout.addLayout(actions)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
