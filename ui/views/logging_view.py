"""
Vue onglet Enregistrement — config, graphique temps réel.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QComboBox,
    QLineEdit,
    QFrame,
)


class LoggingView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel(
            "Enregistrement des mesures du multimètre OWON à intervalle régulier : valeur, unité et mode "
            "dans un fichier CSV horodaté. Le générateur n'est pas enregistré."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-style: italic; padding: 4px 0;")
        layout.addWidget(info)

        config_gb = QGroupBox("Configuration enregistrement")
        config_layout = QHBoxLayout(config_gb)
        config_layout.addWidget(QLabel("Intervalle"))
        config_layout.addWidget(QSpinBox())
        config_layout.addWidget(QComboBox())
        config_layout.addWidget(QLabel("Durée"))
        config_layout.addWidget(QSpinBox())
        config_layout.addWidget(QComboBox())
        config_layout.addWidget(QLabel("Dossier"))
        config_layout.addWidget(QLineEdit())
        config_layout.addWidget(QPushButton("Parcourir"))
        layout.addWidget(config_gb)

        graph_placeholder = QFrame()
        graph_placeholder.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        graph_placeholder.setMinimumHeight(250)
        graph_placeholder.setStyleSheet("background-color: #2d2d2d;")
        layout.addWidget(QLabel("Graphique temps réel (courbe valeur = f(temps))"))
        layout.addWidget(graph_placeholder)

        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Démarrer"))
        btns.addWidget(QPushButton("Arrêter"))
        btns.addWidget(QPushButton("Mettre en pause"))
        btns.addWidget(QPushButton("Ouvrir fichier"))
        btns.addWidget(QPushButton("Exporter image"))
        layout.addLayout(btns)
        layout.addStretch()
