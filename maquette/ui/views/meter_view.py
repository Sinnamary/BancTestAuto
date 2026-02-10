"""
Vue onglet Multimètre — maquette alignée sur l'onglet réel.
Aucune logique de mesure, uniquement la structure et les widgets d'interface.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
)
from PyQt6.QtCore import Qt

from ui.widgets import (
    ModeBar,
    MeasurementDisplay,
    RangeSelector,
    RateSelector,
    MathPanel,
    AdvancedParamsPanel,
    HistoryTable,
)


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

        # --- Barre de modes (identique à l'onglet réel) ---
        self._mode_bar = ModeBar()
        layout.addWidget(self._mode_bar)

        # --- Affichage principal + secondaire ---
        self._display = MeasurementDisplay()
        # Valeurs factices pour la maquette
        self._display.set_value("12.345 V")
        self._display.set_secondary("1.234 kHz")
        layout.addWidget(self._display)

        # --- Plage + Vitesse + Math ---
        row = QWidget()
        row_layout = QHBoxLayout(row)
        self._range_selector = RangeSelector()
        # Plages factices pour illustrer le fonctionnement
        self._range_selector.set_ranges(
            [("500 mV", 0.5), ("5 V", 5.0), ("50 V", 50.0), ("500 V", 500.0)]
        )
        row_layout.addWidget(self._range_selector)

        self._rate_selector = RateSelector()
        row_layout.addWidget(self._rate_selector)

        self._math_panel = MathPanel()
        layout.addWidget(row)
        row_layout.addWidget(self._math_panel)

        # --- Paramètres avancés (RTD, continuité, buzzer) ---
        self._advanced_params = AdvancedParamsPanel()
        layout.addWidget(self._advanced_params)

        # --- Historique ---
        self._history_widget = HistoryTable()
        # Quelques lignes factices pour la maquette
        self._history_widget.set_rows(
            [("12.340", "V"), ("12.341", "V"), ("12.342", "V")]
        )
        layout.addWidget(self._history_widget)

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
