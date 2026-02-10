"""
Formulaire réutilisable pour la configuration série (port, débit, timeouts, log).
Utilisé par SerialConfigDialog pour les onglets Multimètre et Générateur.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
)

try:
    from core.device_detection import list_serial_ports
except ImportError:
    def list_serial_ports():
        return []


class SerialConfigForm:
    """
    Encapsule un formulaire (port, débit, timeouts, log) et expose
    un widget et get_values() pour récupérer les champs.
    """
    DEFAULT_BAUDRATES = [9600, 19200, 38400, 57600, 115200]

    def __init__(self, config: dict, baudrate_options: list = None):
        self._config = dict(config)
        baud_opts = baudrate_options or self.DEFAULT_BAUDRATES

        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        for p in list_serial_ports():
            self._port_combo.addItem(p)
        self._port_combo.setCurrentText(self._config.get("port", "COM1"))

        self._baud_combo = QComboBox()
        for b in baud_opts:
            self._baud_combo.addItem(str(b))
        self._baud_combo.setCurrentText(str(self._config.get("baudrate", 9600)))

        self._timeout_spin = QDoubleSpinBox()
        self._timeout_spin.setRange(0.5, 30)
        self._timeout_spin.setValue(float(self._config.get("timeout", 2)))
        self._timeout_spin.setDecimals(1)

        self._write_timeout_spin = QDoubleSpinBox()
        self._write_timeout_spin.setRange(0.5, 30)
        self._write_timeout_spin.setValue(float(self._config.get("write_timeout", 2)))
        self._write_timeout_spin.setDecimals(1)

        self._log_check = QCheckBox()
        self._log_check.setChecked(bool(self._config.get("log_exchanges", False)))

        self._widget = QWidget()
        form = QFormLayout(self._widget)
        form.addRow("Port", self._port_combo)
        form.addRow("Débit (bauds)", self._baud_combo)
        form.addRow("Timeout lecture (s)", self._timeout_spin)
        form.addRow("Timeout écriture (s)", self._write_timeout_spin)
        form.addRow("Logger les échanges", self._log_check)

    def widget(self) -> QWidget:
        return self._widget

    def get_values(self) -> dict:
        return {
            "port": self._port_combo.currentText().strip(),
            "baudrate": int(self._baud_combo.currentText()),
            "bytesize": self._config.get("bytesize", 8),
            "parity": self._config.get("parity", "N"),
            "stopbits": self._config.get("stopbits", 1),
            "timeout": self._timeout_spin.value(),
            "write_timeout": self._write_timeout_spin.value(),
            "log_exchanges": self._log_check.isChecked(),
        }
