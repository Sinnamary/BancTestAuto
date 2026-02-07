"""
Fenêtre d'aide avec contenu Markdown et recherche (Suivant / Précédent).
Charge docs/AIDE.md, le convertit en HTML et l'affiche dans un QTextBrowser.
"""
from pathlib import Path

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QKeySequence, QShortcut, QTextDocument, QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QLineEdit,
    QPushButton,
    QLabel,
    QSizePolicy,
    QFrame,
)

# Conversion Markdown → HTML (optionnel : utiliser le package markdown si disponible)
def _md_to_html(md_path: Path) -> str:
    """Charge le fichier Markdown et le convertit en HTML."""
    if not md_path.exists():
        return f"<p>Fichier d'aide introuvable : <code>{md_path}</code></p>"
    try:
        raw = md_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"<p>Erreur de lecture : {e!s}</p>"
    try:
        import markdown
        html = markdown.markdown(raw, extensions=["extra"])
    except ImportError:
        # Fallback simple : échapper HTML et remplacer \n par <br/>
        import html as html_module
        html = "<pre style='white-space: pre-wrap;'>" + html_module.escape(raw) + "</pre>"
    base_css = """
    <style>
    body { font-family: Segoe UI, Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 12px; }
    h1 { font-size: 1.4em; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
    h2 { font-size: 1.2em; margin-top: 1em; }
    h3 { font-size: 1.05em; }
    code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; }
    pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
    table { border-collapse: collapse; margin: 0.5em 0; }
    th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: left; }
    th { background: #e8e8e8; }
    a { color: #0066cc; }
    </style>
    """
    return base_css + html


class HelpDialog(QDialog):
    """Dialogue d'aide : affichage du manuel (AIDE.md) avec recherche dans le texte."""

    def __init__(self, help_path: Path = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aide — Banc de test automatique")
        self.setMinimumSize(720, 560)
        self.resize(860, 640)

        self._help_path = help_path or self._default_help_path()
        self._browser = QTextBrowser(self)
        self._browser.setOpenExternalLinks(True)
        self._browser.setReadOnly(True)

        layout = QVBoxLayout(self)

        # Barre de recherche
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 6, 8, 6)
        search_layout.addWidget(QLabel("Rechercher :"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Saisir un mot ou une expression...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.setMinimumWidth(220)
        self._search_edit.returnPressed.connect(self._find_next)
        search_layout.addWidget(self._search_edit)
        self._btn_next = QPushButton("Suivant")
        self._btn_next.setShortcut("F3")
        self._btn_next.clicked.connect(self._find_next)
        search_layout.addWidget(self._btn_next)
        self._btn_prev = QPushButton("Précédent")
        self._btn_prev.setShortcut("Shift+F3")
        self._btn_prev.clicked.connect(self._find_previous)
        search_layout.addWidget(self._btn_prev)
        search_layout.addStretch()
        self._btn_next.setEnabled(False)
        self._btn_prev.setEnabled(False)
        layout.addWidget(search_frame)

        layout.addWidget(self._browser)

        # Charger le contenu
        html = _md_to_html(self._help_path)
        self._browser.setHtml(html)

        # Raccourci Ctrl+F pour focus recherche
        sc = QShortcut(QKeySequence("Ctrl+F"), self)
        sc.activated.connect(self._focus_search)
        sc = QShortcut(QKeySequence("Ctrl+L"), self)
        sc.activated.connect(self._focus_search)
        self._search_edit.textChanged.connect(self._on_search_text_changed)

    def _default_help_path(self) -> Path:
        """Chemin par défaut vers docs/AIDE.md (racine = parent de ui/)."""
        # ui/dialogs/help_dialog.py → racine = parent.parent.parent
        this_file = Path(__file__).resolve()
        root = this_file.parent.parent.parent
        return root / "docs" / "AIDE.md"

    def _focus_search(self):
        self._search_edit.setFocus()
        self._search_edit.selectAll()

    def _on_search_text_changed(self, text):
        enabled = bool(text and text.strip())
        self._btn_next.setEnabled(enabled)
        self._btn_prev.setEnabled(enabled)

    def _find_next(self):
        self._do_find(backward=False)

    def _find_previous(self):
        self._do_find(backward=True)

    def _do_find(self, backward: bool):
        text = self._search_edit.text().strip()
        if not text:
            return
        cursor = self._browser.textCursor()
        if backward:
            flags = QTextDocument.FindFlag.FindBackward
        else:
            flags = QTextDocument.FindFlag(0)
        # Chercher à partir de la position actuelle (ou du début si backward)
        regex = QRegularExpression(QRegularExpression.escape(text))
        found = self._browser.find(regex, flags)
        if not found:
            # Boucler : repartir du début (ou de la fin si backward)
            cursor = self._browser.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._browser.setTextCursor(cursor)
            found = self._browser.find(regex, flags)
        if not found and self._browser.textCursor().hasSelection():
            # Garder la sélection précédente si plus de résultat
            pass
