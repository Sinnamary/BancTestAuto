"""
Construction des menus de la fenêtre principale.
Délègue depuis MainWindow._build_menu() pour réduire la complexité.
"""
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence


def build_file_menu(main_window):
    """Construit le menu Fichier (config, CSV, log, quitter)."""
    file_menu = main_window.menuBar().addMenu("Fichier")
    file_menu.addAction("Ouvrir config...", main_window._on_open_config)
    file_menu.addAction("Ouvrir CSV Banc filtre...", main_window._on_open_bode_csv)
    file_menu.addAction("Sauvegarder config", main_window._on_save_config)
    file_menu.addAction("Enregistrer config sous...", main_window._on_save_config_as)
    file_menu.addSeparator()
    file_menu.addAction("Voir config JSON (lecture seule)", main_window._on_view_config)
    file_menu.addAction("Lire le dernier log", main_window._on_view_latest_log)
    file_menu.addSeparator()
    file_menu.addAction("Quitter", main_window.close)


def build_tools_menu(main_window):
    """Construit le menu Outils (détection équipements)."""
    tools_menu = main_window.menuBar().addMenu("Outils")
    tools_menu.addAction("Détecter les équipements...", main_window._on_detect_devices)


def build_config_menu(main_window):
    """Construit le menu Configuration (thème, niveau de log)."""
    config_menu = main_window.menuBar().addMenu("Configuration")
    theme_menu = config_menu.addMenu("Thème")
    main_window._theme_group = QActionGroup(main_window)
    main_window._theme_group.setExclusive(True)
    main_window._theme_actions = {}
    for label, theme_id in (("Clair", "light"), ("Foncé", "dark")):
        action = QAction(label, main_window, checkable=True)
        action.triggered.connect(lambda checked, t=theme_id: main_window._on_theme(t))
        main_window._theme_group.addAction(action)
        theme_menu.addAction(action)
        main_window._theme_actions[theme_id] = action
    main_window._update_theme_menu()
    config_menu.addSeparator()
    log_level_menu = config_menu.addMenu("Niveau de log")
    main_window._log_level_group = QActionGroup(main_window)
    main_window._log_level_group.setExclusive(True)
    for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        action = QAction(level, main_window, checkable=True)
        action.triggered.connect(lambda checked, l=level: main_window._on_log_level(l))
        main_window._log_level_group.addAction(action)
        log_level_menu.addAction(action)
    main_window._log_level_actions = {a.text(): a for a in main_window._log_level_group.actions()}
    main_window._update_log_level_menu()


def build_help_menu(main_window):
    """Construit le menu Aide (manuel, à propos, docs équipements)."""
    help_menu = main_window.menuBar().addMenu("Aide")
    help_menu.addAction("Manuel", QKeySequence("F1"), main_window._on_help)
    help_menu.addSeparator()
    help_menu.addAction("A propos...", main_window._on_about)
    sub_owon = help_menu.addMenu("Multimètre OWON")
    sub_owon.addAction("Commandes (documentation)", lambda: main_window._on_help_doc("COMMANDES_OWON.md"))
    sub_fy6900 = help_menu.addMenu("Générateur FY6900")
    sub_fy6900.addAction("Commandes (documentation)", lambda: main_window._on_help_doc("COMMANDES_FY6900.md"))
    sub_rs305p = help_menu.addMenu("Alimentation RS305P")
    sub_rs305p.addAction("Commandes (documentation)", lambda: main_window._on_help_doc("COMMANDES_RS305P.md"))
    sub_dos1102 = help_menu.addMenu("Oscilloscope DOS1102")
    sub_dos1102.addAction("Commandes (documentation)", lambda: main_window._on_help_doc("COMMANDES_HANMATEK_DOS1102.md"))
