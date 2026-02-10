"""
Vue maquette « Alimentation ».
Aucune connexion réelle à une RS305P : uniquement l'interface utilisateur.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
)


class PowerSupplyView(QWidget):
    """
    Maquette de l'onglet « Alimentation ».

    Permet de visualiser les paramètres typiques :
    - tension consigne,
    - courant limite,
    - mode sortie (ON/OFF),
    sans piloter réellement un équipement.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        gb = QGroupBox("Alimentation RS305P (maquette)")
        form = QFormLayout(gb)

        self._voltage_spin = QDoubleSpinBox()
        self._voltage_spin.setSuffix(" V")
        self._voltage_spin.setMinimum(0.0)
        self._voltage_spin.setMaximum(30.0)
        self._voltage_spin.setValue(5.0)
        form.addRow("Tension consigne :", self._voltage_spin)

        self._current_spin = QDoubleSpinBox()
        self._current_spin.setSuffix(" A")
        self._current_spin.setMinimum(0.0)
        self._current_spin.setMaximum(5.0)
        self._current_spin.setSingleStep(0.1)
        self._current_spin.setValue(1.0)
        form.addRow("Courant limite :", self._current_spin)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Sortie OFF", "Sortie ON"])
        form.addRow("Sortie :", self._mode_combo)

        self._apply_btn = QPushButton("Appliquer (maquette)")
        self._apply_btn.setEnabled(False)
        form.addRow("", self._apply_btn)

        layout.addWidget(gb)

        info = QLabel(
            "Cette vue est une maquette : la sortie n'est pas réellement pilotée.\n"
            "Les champs servent uniquement à valider l'ergonomie avant intégration."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()

