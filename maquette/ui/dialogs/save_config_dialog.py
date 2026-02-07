"""
Dialogue de sauvegarde de la configuration JSON — maquette.
À intégrer avec le chemin par défaut config/config.json.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QDialogButtonBox,
)


class SaveConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sauvegarder la configuration")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("config/config.json")
        form.addRow("Fichier", self._path_edit)
        browse = QPushButton("Parcourir...")
        form.addRow("", browse)
        layout.addLayout(form)
        layout.addWidget(QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        ))
