"""
Dialogue pour afficher le contenu du fichier config.json en lecture seule (brut).
"""
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPlainTextEdit,
    QLabel,
    QDialogButtonBox,
)


class ViewConfigDialog(QDialog):
    """Affiche le JSON de configuration en lecture seule."""

    def __init__(self, config_path: Path = None, config_dict: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Config JSON (lecture seule)")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        self._path_label = QLabel()
        self._path_label.setStyleSheet("color: #666;")
        layout.addWidget(self._path_label)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self._text)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

        # Remplir le contenu
        path = config_path or Path("config/config.json")
        self._path_label.setText(f"Fichier : {path.resolve()}")

        if config_dict is not None:
            try:
                raw = json.dumps(config_dict, indent=2, ensure_ascii=False)
                self._text.setPlainText(raw)
            except Exception:
                self._text.setPlainText("(Erreur formatage JSON)")
        elif path.exists():
            try:
                text = path.read_text(encoding="utf-8")
                self._text.setPlainText(text)
            except Exception as e:
                self._text.setPlainText(f"(Erreur lecture : {e})")
        else:
            self._text.setPlainText("(Fichier absent)")
