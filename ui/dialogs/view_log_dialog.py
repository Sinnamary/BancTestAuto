"""
Dialogue pour afficher le contenu du dernier fichier de log (lecture seule).
"""
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPlainTextEdit,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QDialogButtonBox,
)


def _open_path_in_system(path: Path) -> bool:
    """Ouvre le fichier ou le dossier avec l'application par défaut du système."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
        return True
    except Exception:
        return False


class ViewLogDialog(QDialog):
    """Affiche le contenu d'un fichier de log en lecture seule."""

    def __init__(self, log_path: Path, parent=None):
        super().__init__(parent)
        self._log_path = Path(log_path)
        self.setWindowTitle("Dernier log")
        self.setMinimumSize(600, 450)
        self.resize(750, 550)

        layout = QVBoxLayout(self)
        self._path_label = QLabel()
        self._path_label.setStyleSheet("color: #666;")
        self._path_label.setText(f"Fichier : {self._log_path.resolve()}")
        layout.addWidget(self._path_label)

        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self._text)

        btn_layout = QHBoxLayout()
        open_file_btn = QPushButton("Ouvrir le fichier avec l'éditeur par défaut")
        open_file_btn.clicked.connect(self._on_open_file)
        btn_layout.addWidget(open_file_btn)
        open_folder_btn = QPushButton("Ouvrir le dossier des logs")
        open_folder_btn.clicked.connect(self._on_open_folder)
        btn_layout.addWidget(open_folder_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

        self._load_content()

    def _load_content(self) -> None:
        if not self._log_path.exists():
            self._text.setPlainText("(Fichier introuvable)")
            return
        try:
            text = self._log_path.read_text(encoding="utf-8", errors="replace")
            self._text.setPlainText(text)
            self._text.moveCursor(QTextCursor.MoveOperation.End)
        except Exception as e:
            self._text.setPlainText(f"(Erreur lecture : {e})")

    def _on_open_file(self) -> None:
        _open_path_in_system(self._log_path)

    def _on_open_folder(self) -> None:
        folder = self._log_path.parent
        if folder.exists():
            _open_path_in_system(folder)
