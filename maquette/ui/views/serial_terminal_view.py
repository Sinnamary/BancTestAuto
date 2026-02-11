"""
Vue onglet Terminal série (maquette) : uniquement un sélecteur d'équipement connecté.
Pas de connexion propre : on utilise la connexion déjà ouverte par la barre (Multimètre,
Générateur, Alimentation, Oscilloscope). Envoi/réception avec CR/LF en fin de chaîne.
"""
from typing import Callable, List, Tuple, Any, Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor

from core.app_logger import get_logger

logger = get_logger(__name__)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
)


class SerialTerminalView(QWidget):
    """Onglet Terminal série : combo Équipement (Multimètre, Générateur, Alimentation, Oscilloscope) — rien d'autre."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection_provider: Optional[Callable[[], List[Tuple[Any, str, Any]]]] = None
        self._equipment_list: List[Tuple[Any, str, Any]] = []
        self._equipment_conn: Any = None
        self._read_timer = QTimer(self)
        self._read_timer.timeout.connect(self._poll_serial)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Équipement : uniquement la combo (connexion déjà ouverte par la barre) ---
        eq_gb = QGroupBox("Utiliser la connexion d'un équipement connecté")
        eq_layout = QHBoxLayout(eq_gb)
        eq_layout.addWidget(QLabel("Équipement:"))
        self._equipment_combo = QComboBox()
        self._equipment_combo.setMinimumWidth(160)
        self._equipment_combo.setPlaceholderText("Aucun équipement connecté")
        self._equipment_combo.setToolTip(
            "Liste des équipements déjà connectés par la barre. Choisir un équipement pour envoyer/recevoir sur sa connexion."
        )
        self._equipment_combo.currentIndexChanged.connect(self._on_equipment_selection_changed)
        eq_layout.addWidget(self._equipment_combo)
        self._equipment_refresh_btn = QPushButton("Actualiser")
        self._equipment_refresh_btn.clicked.connect(self._refresh_equipment_list)
        eq_layout.addWidget(self._equipment_refresh_btn)
        self._status_label = QLabel("Aucun équipement connecté (connectez depuis la barre)")
        eq_layout.addWidget(self._status_label)
        eq_layout.addStretch()
        layout.addWidget(eq_gb)

        # --- Options d'envoi : CR / LF en fin de chaîne ---
        send_opts_gb = QGroupBox("Envoi : fin de chaîne")
        send_opts_layout = QHBoxLayout(send_opts_gb)
        self._check_cr = QCheckBox("Ajouter CR (\\r) en fin de chaîne")
        self._check_cr.setChecked(False)
        send_opts_layout.addWidget(self._check_cr)
        self._check_lf = QCheckBox("Ajouter LF (\\n) en fin de chaîne")
        self._check_lf.setChecked(True)
        send_opts_layout.addWidget(self._check_lf)
        send_opts_layout.addStretch()
        layout.addWidget(send_opts_gb)

        # --- Envoi ---
        send_gb = QGroupBox("Envoyer")
        send_layout = QHBoxLayout(send_gb)
        self._command_edit = QLineEdit()
        self._command_edit.setPlaceholderText("Commande à envoyer...")
        self._command_edit.returnPressed.connect(self._send_command)
        send_layout.addWidget(self._command_edit)
        self._send_btn = QPushButton("Envoyer")
        self._send_btn.clicked.connect(self._send_command)
        self._send_btn.setEnabled(False)
        send_layout.addWidget(self._send_btn)
        self._clear_cmd_btn = QPushButton("Effacer")
        self._clear_cmd_btn.clicked.connect(self._command_edit.clear)
        send_layout.addWidget(self._clear_cmd_btn)
        layout.addWidget(send_gb)

        # --- Réception ---
        recv_gb = QGroupBox("Réception")
        recv_layout = QVBoxLayout(recv_gb)
        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setPlaceholderText("Données reçues...")
        recv_layout.addWidget(self._output_text)
        clear_btn = QPushButton("Vider")
        clear_btn.clicked.connect(self._output_text.clear)
        recv_layout.addWidget(clear_btn)
        layout.addWidget(recv_gb)

    def set_connection_provider(self, provider: Optional[Callable[[], List[Tuple[Any, str, Any]]]]) -> None:
        """Injecte le fournisseur de liste d'équipements connectés (kind, display_name, conn)."""
        self._connection_provider = provider
        self._refresh_equipment_list()

    def refresh_equipment_list(self) -> None:
        """Rafraîchit la liste des équipements (appelé par la fenêtre après mise à jour des connexions)."""
        self._refresh_equipment_list()

    def _refresh_equipment_list(self) -> None:
        self._equipment_list = []
        if self._connection_provider:
            try:
                self._equipment_list = self._connection_provider()
            except Exception as e:
                logger.debug("Terminal maquette: refresh equipment list failed: %s", e)
        self._equipment_combo.clear()
        for _kind, display_name, _conn in self._equipment_list:
            self._equipment_combo.addItem(display_name)
        if self._equipment_combo.count() > 0 and self._equipment_conn is None:
            self._equipment_combo.setCurrentIndex(0)
        elif self._equipment_combo.count() == 0:
            self._equipment_conn = None
        self._on_equipment_selection_changed()

    def _on_equipment_selection_changed(self) -> None:
        idx = self._equipment_combo.currentIndex()
        if 0 <= idx < len(self._equipment_list):
            _kind, _name, conn = self._equipment_list[idx]
            self._equipment_conn = conn if (conn and getattr(conn, "is_open", lambda: False)()) else None
        else:
            self._equipment_conn = None
        self._update_equipment_status_label()
        self._send_btn.setEnabled(self._equipment_conn is not None)
        if self._equipment_conn and not self._read_timer.isActive():
            self._read_timer.start(50)
        elif not self._equipment_conn:
            self._read_timer.stop()

    def _update_equipment_status_label(self) -> None:
        if self._equipment_conn:
            idx = self._equipment_combo.currentIndex()
            name = self._equipment_combo.currentText() if 0 <= idx < self._equipment_combo.count() else "Équipement"
            self._status_label.setText(f"Envoi/réception sur : {name}")
        else:
            self._status_label.setText(
                "Aucun équipement connecté (connectez depuis la barre)"
                if self._equipment_combo.count() == 0
                else "Choisissez un équipement dans la liste"
            )

    def _get_current_connection(self):
        conn = None
        if self._equipment_conn and getattr(self._equipment_conn, "is_open", lambda: False)():
            conn = self._equipment_conn
        return conn

    def _send_command(self):
        conn = self._get_current_connection()
        if conn is None:
            logger.debug("Terminal maquette: _send_command ignoré (aucun équipement)")
            return
        text = self._command_edit.text()
        data = text.encode("utf-8", errors="replace")
        if self._check_cr.isChecked():
            data += b"\r"
        if self._check_lf.isChecked():
            data += b"\n"
        if not data:
            return
        try:
            conn.write(data)
            self._append_received(f"> {text}\n")
        except Exception as e:
            logger.debug("Terminal maquette: write() erreur: %s", e, exc_info=True)
            QMessageBox.warning(self, "Terminal série", f"Erreur envoi : {e}")

    def _poll_serial(self):
        conn = self._get_current_connection()
        if not conn:
            return
        try:
            if not getattr(conn, "is_open", lambda: False)():
                return
            n = getattr(conn, "in_waiting", lambda: 0)()
            if n > 0:
                data = conn.read(min(n, 1024))
                if data:
                    try:
                        text = data.decode("utf-8", errors="replace")
                    except Exception:
                        text = data.hex(" ")
                    self._append_received(text)
        except Exception:
            pass

    def _append_received(self, text: str):
        self._output_text.moveCursor(QTextCursor.MoveOperation.End)
        self._output_text.insertPlainText(text)
        self._output_text.moveCursor(QTextCursor.MoveOperation.End)

    def load_config(self, config: dict):
        """Compatibilité : la maquette n'utilise pas la config pour le terminal (uniquement la barre)."""
        pass

    def disconnect_serial(self):
        """Arrêt du timer de lecture (pas de connexion propre à fermer)."""
        self._read_timer.stop()
        self._equipment_conn = None
        self._update_equipment_status_label()

    def closeEvent(self, event):
        self.disconnect_serial()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_equipment_list()
