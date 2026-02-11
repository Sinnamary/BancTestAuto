"""
Dialogue « À propos » : présentation type « À PROPOS » avec barre titre, bandeau nom,
panneau d'infos blanc, zone équipements et bouton OK style 3D.
"""
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


def _get_qt_version() -> str:
    """Retourne la version de PyQt6 si disponible."""
    try:
        from PyQt6.QtCore import qVersion
        return qVersion()
    except Exception:
        return "—"


def _gradient_header_style(obj_name: str) -> str:
    """Style dégradé bleu (barre titre / bandeau nom)."""
    return f"""
        QFrame#{obj_name} {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0d47a1, stop:0.5 #1565c0, stop:1 #1976d2);
            border: none;
        }}
    """


class AboutDialog(QDialog):
    """Présentation type référence : barre À PROPOS, nom centré, panneau blanc, zone équipements, bouton OK 3D."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos")
        self.setMinimumWidth(480)
        self.setMinimumHeight(420)
        self.setStyleSheet("QDialog { background: #ffffff; }")

        try:
            from core.version import APP_NAME, __version__, get_version_date
            __version_date__ = get_version_date()
        except ImportError:
            APP_NAME = "Banc de test automatique"
            __version__ = "—"
            __version_date__ = "—"

        qt_ver = _get_qt_version()
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # —— Barre type « titre » : icône + À PROPOS ——
        title_bar = QFrame()
        title_bar.setObjectName("aboutTitleBar")
        title_bar.setStyleSheet(_gradient_header_style("aboutTitleBar"))
        title_bar.setFixedHeight(44)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(10)
        icon_label = QLabel("⚙")
        icon_label.setStyleSheet("color: #ffffff; font-size: 18px; background: transparent; border: none;")
        tb_layout.addWidget(icon_label)
        tit = QLabel("À PROPOS")
        tit.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; letter-spacing: 1px; background: transparent; border: none;")
        tb_layout.addWidget(tit)
        tb_layout.addStretch()
        layout.addWidget(title_bar)

        # —— Bandeau nom application (centré) ——
        name_band = QFrame()
        name_band.setObjectName("aboutNameBand")
        name_band.setStyleSheet(_gradient_header_style("aboutNameBand"))
        name_band.setFixedHeight(64)
        nb_layout = QVBoxLayout(name_band)
        nb_layout.setContentsMargins(24, 12, 24, 12)
        app_name = QLabel(APP_NAME)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold; background: transparent; border: none;")
        app_name.setWordWrap(True)
        nb_layout.addWidget(app_name)
        layout.addWidget(name_band)

        # —— Panneau blanc : Version, Date, Environnement ——
        white_panel = QFrame()
        white_panel.setStyleSheet("QFrame { background: #ffffff; padding: 0; border: none; }")
        wp_layout = QVBoxLayout(white_panel)
        wp_layout.setContentsMargins(24, 20, 24, 20)
        wp_layout.setSpacing(10)

        ver_label = QLabel(f"Version {__version__}")
        ver_label.setStyleSheet("color: #212121; font-size: 14px; font-weight: bold;")
        wp_layout.addWidget(ver_label)
        date_label = QLabel(f"Date de release : {__version_date__}")
        date_label.setStyleSheet("color: #424242; font-size: 13px;")
        wp_layout.addWidget(date_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e0e0e0; border: none; max-height: 1px;")
        wp_layout.addWidget(sep)
        wp_layout.addSpacing(12)

        env_row = QHBoxLayout()
        env_row.setSpacing(8)
        env_icon = QLabel("⚙")
        env_icon.setStyleSheet("color: #1565c0; font-size: 14px;")
        env_row.addWidget(env_icon)
        env_title = QLabel("Environnement")
        env_title.setStyleSheet("color: #212121; font-size: 13px; font-weight: bold;")
        env_row.addWidget(env_title)
        env_row.addStretch()
        wp_layout.addLayout(env_row)
        env_text = QLabel(f"Python {py_ver}  ·  Qt {qt_ver}")
        env_text.setStyleSheet("color: #424242; font-size: 13px; margin-left: 22px;")
        wp_layout.addWidget(env_text)

        layout.addWidget(white_panel)

        # —— Zone illustration équipements (fond gris, texte ou image) ——
        equip_frame = QFrame()
        equip_frame.setStyleSheet("""
            QFrame {
                background: #eceff1;
                border: none;
                min-height: 100px;
            }
        """)
        equip_frame.setMinimumHeight(100)
        eq_layout = QVBoxLayout(equip_frame)
        eq_layout.setContentsMargins(16, 16, 16, 16)
        eq_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Image optionnelle : placer un fichier resources/about_equipment.png pour l'afficher
        img_paths = [
            Path(__file__).resolve().parent.parent.parent / "resources" / "about_equipment.png",
            Path(__file__).resolve().parent.parent.parent / "docs" / "about_equipment.png",
        ]
        pix = None
        for p in img_paths:
            if p.exists():
                try:
                    pix = QPixmap(str(p))
                    if not pix.isNull():
                        break
                except Exception:
                    pass
        if pix and not pix.isNull():
            img_label = QLabel()
            img_label.setPixmap(pix.scaledToWidth(440, Qt.TransformationMode.SmoothTransformation))
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            eq_layout.addWidget(img_label)
        else:
            equip_text = QLabel("Multimètre OWON  ·  Générateur FY6900  ·  Alimentation RS305P")
            equip_text.setStyleSheet("color: #546e7a; font-size: 12px;")
            equip_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            equip_text.setWordWrap(True)
            eq_layout.addWidget(equip_text)
        layout.addWidget(equip_frame)

        # —— Bouton OK style 3D (dégradé + ombre) ——
        btn_container = QFrame()
        btn_container.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        btn_container.setFixedHeight(56)
        bc_layout = QVBoxLayout(btn_container)
        bc_layout.setContentsMargins(24, 12, 24, 16)
        bc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 36)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #0d47a1);
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e88e5, stop:1 #1565c0);
            }
            QPushButton:pressed {
                background: #0d47a1;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        bc_layout.addWidget(ok_btn)
        layout.addWidget(btn_container)
