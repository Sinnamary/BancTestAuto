"""
Vue onglet Banc de test filtre — maquette (tableau et graphique vides ou factices).
Permet de choisir la voie du générateur FY6900 (1 ou 2) pour le balayage.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QTableWidget,
    QProgressBar,
    QFrame,
    QRadioButton,
    QButtonGroup,
)


class FilterTestView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        config_gb = QGroupBox("Balayage en fréquence")
        config_layout = QVBoxLayout(config_gb)

        # Ligne 1 : Voie générateur + f_min, f_max, points, échelle
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Voie générateur FY6900 :"))
        self._channel_group = QButtonGroup(self)
        self._channel_1 = QRadioButton("Voie 1")
        self._channel_2 = QRadioButton("Voie 2")
        self._channel_1.setChecked(True)
        self._channel_group.addButton(self._channel_1)
        self._channel_group.addButton(self._channel_2)
        row1.addWidget(self._channel_1)
        row1.addWidget(self._channel_2)
        row1.addSpacing(24)
        row1.addWidget(QLabel("f_min (Hz)"))
        row1.addWidget(QDoubleSpinBox())
        row1.addWidget(QLabel("f_max (Hz)"))
        row1.addWidget(QDoubleSpinBox())
        row1.addWidget(QLabel("Points"))
        row1.addWidget(QSpinBox())
        row1.addWidget(QLabel("Échelle"))
        row1.addWidget(QComboBox())
        row1.addStretch()
        config_layout.addLayout(row1)

        # Ligne 2 : Délai, Ue
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Délai (ms)"))
        row2.addWidget(QSpinBox())
        row2.addWidget(QLabel("Ue (V RMS)"))
        row2.addWidget(QDoubleSpinBox())
        row2.addStretch()
        config_layout.addLayout(row2)

        layout.addWidget(config_gb)

        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Démarrer balayage"))
        btns.addWidget(QPushButton("Arrêter"))
        btns.addWidget(QPushButton("Exporter CSV"))
        btns.addWidget(QPushButton("Exporter graphique"))
        layout.addLayout(btns)

        self._progress = QProgressBar()
        layout.addWidget(self._progress)

        # Tableau
        table_gb = QGroupBox("Résultats")
        table_layout = QVBoxLayout(table_gb)
        self._results_table = QTableWidget(0, 4)
        self._results_table.setHorizontalHeaderLabels(["f (Hz)", "Us (V)", "Us/Ue", "Gain (dB)"])
        table_layout.addWidget(self._results_table)
        layout.addWidget(table_gb)

        # Graphique Bode : rappel des échelles (fréquence toujours en log ; Y = linéaire ou dB)
        graph_desc = QLabel(
            "Graphique Bode — Axe X : fréquence (Hz), toujours en échelle logarithmique. "
            "Axe Y : gain linéaire (Us/Ue) ou gain en dB (20×log₁₀(Us/Ue)), au choix ci‑dessous."
        )
        graph_desc.setWordWrap(True)
        graph_desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(graph_desc)

        # Choix de l’ordonnée (linéaire ou dB)
        y_axis_gb = QGroupBox("Ordonnée (Y) du graphique")
        y_axis_layout = QHBoxLayout(y_axis_gb)
        self._y_axis_group = QButtonGroup(self)
        self._y_linear = QRadioButton("Gain linéaire (Us/Ue) — échelle linéaire")
        self._y_db = QRadioButton("Gain en dB (20×log₁₀(Us/Ue)) — représentation logarithmique")
        self._y_db.setChecked(True)
        self._y_axis_group.addButton(self._y_linear)
        self._y_axis_group.addButton(self._y_db)
        y_axis_layout.addWidget(self._y_linear)
        y_axis_layout.addWidget(self._y_db)
        layout.addWidget(y_axis_gb)

        # Zone graphique factice
        graph_placeholder = QFrame()
        graph_placeholder.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        graph_placeholder.setMinimumHeight(200)
        graph_placeholder.setStyleSheet("background-color: #2d2d2d;")
        layout.addWidget(graph_placeholder)
        layout.addStretch()

    def get_generator_channel(self) -> int:
        """Retourne la voie du générateur utilisée pour le balayage (1 ou 2)."""
        return 2 if self._channel_2.isChecked() else 1

    def is_gain_in_db(self) -> bool:
        """True si l’ordonnée du graphique est en dB (20×log₁₀(Us/Ue)), False si gain linéaire Us/Ue."""
        return self._y_db.isChecked()
