"""
Vue maquette « Calcul filtre ».
Ne contient que l'ossature visuelle, sans logique métier ni accès à core/.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QFormLayout,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
)


class FilterCalculatorView(QWidget):
    """
    Maquette de l'onglet « Calcul filtre ».

    Objectif : visualiser les principaux paramètres qu'on pourra proposer
    (type de filtre, ordre, fréquences, impédances, etc.) sans effectuer
    de calcul réel.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        gb = QGroupBox("Paramètres de filtre (maquette)")
        form = QFormLayout(gb)

        self._type_combo = QComboBox()
        self._type_combo.addItems(
            [
                "Passe-bas",
                "Passe-haut",
                "Passe-bande",
                "Coupe-bande",
            ]
        )
        form.addRow("Type de filtre :", self._type_combo)

        self._order_spin = QDoubleSpinBox()
        self._order_spin.setDecimals(0)
        self._order_spin.setMinimum(1)
        self._order_spin.setMaximum(8)
        self._order_spin.setValue(2)
        form.addRow("Ordre :", self._order_spin)

        self._f_cut_spin = QDoubleSpinBox()
        self._f_cut_spin.setSuffix(" Hz")
        self._f_cut_spin.setMinimum(0.1)
        self._f_cut_spin.setMaximum(10_000_000)
        self._f_cut_spin.setValue(1000.0)
        form.addRow("Fréquence de coupure :", self._f_cut_spin)

        self._z_source_spin = QDoubleSpinBox()
        self._z_source_spin.setSuffix(" Ω")
        self._z_source_spin.setMinimum(1.0)
        self._z_source_spin.setMaximum(1_000_000)
        self._z_source_spin.setValue(50.0)
        form.addRow("Impédance source :", self._z_source_spin)

        self._z_load_spin = QDoubleSpinBox()
        self._z_load_spin.setSuffix(" Ω")
        self._z_load_spin.setMinimum(1.0)
        self._z_load_spin.setMaximum(1_000_000)
        self._z_load_spin.setValue(10_000.0)
        form.addRow("Impédance charge :", self._z_load_spin)

        self._topology_combo = QComboBox()
        self._topology_combo.addItems(
            [
                "Sallen-Key",
                "RC simple",
                "Multiple feedback",
                "Autre / à définir",
            ]
        )
        form.addRow("Topologie :", self._topology_combo)

        self._placeholder_btn = QPushButton("Calculer (maquette)")
        self._placeholder_btn.setEnabled(False)
        form.addRow("", self._placeholder_btn)

        layout.addWidget(gb)

        info = QLabel(
            "Cette vue est une maquette :\n"
            "- aucun calcul n'est réalisé,\n"
            "- les champs permettent surtout de visualiser les paramètres disponibles.\n"
            "L'implémentation réelle utilisera ces paramètres pour générer les valeurs de composants."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()

