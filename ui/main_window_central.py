"""
Construction du contenu central : barre de connexion, séparateur, onglets.
Délègue depuis MainWindow._build_central() pour réduire la complexité.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QFrame,
)
from ui.widgets import ConnectionStatusBar
from ui.views import (
    MeterView,
    GeneratorView,
    LoggingView,
    FilterTestView,
    FilterCalculatorView,
    PowerSupplyView,
    SerialTerminalView,
    OscilloscopeView,
)


def build_central_widget(main_window):
    """
    Crée le widget central : barre de connexion, séparateur, QTabWidget avec les vues.
    Définit sur main_window : _connection_bar, _tabs, _oscilloscope_view, _filter_test_view,
    _power_supply_view, _serial_terminal_view. Retourne le widget central.
    """
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    main_window._connection_bar = ConnectionStatusBar(main_window)
    layout.addWidget(main_window._connection_bar)

    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    separator.setStyleSheet("background-color: #555; max-height: 1px; margin: 2px 8px;")
    separator.setFixedHeight(1)
    layout.addWidget(separator)

    main_window._tabs = QTabWidget()
    main_window._tabs.addTab(MeterView(), "Multimètre")
    main_window._tabs.addTab(GeneratorView(), "Générateur")
    main_window._oscilloscope_view = OscilloscopeView()
    main_window._tabs.addTab(main_window._oscilloscope_view, "Oscilloscope")
    main_window._filter_test_view = FilterTestView()
    main_window._tabs.addTab(main_window._filter_test_view, "Banc filtre")
    main_window._tabs.addTab(FilterCalculatorView(), "Calcul filtre")
    main_window._tabs.addTab(LoggingView(), "Enregistrement")
    main_window._power_supply_view = PowerSupplyView()
    main_window._tabs.addTab(main_window._power_supply_view, "Alimentation")
    main_window._serial_terminal_view = SerialTerminalView()
    main_window._tabs.addTab(main_window._serial_terminal_view, "Terminal série")
    layout.addWidget(main_window._tabs)

    return central
