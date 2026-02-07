"""
Dialogue de configuration série : port, débit, timeouts, log.
Pour multimètre et/ou générateur ; charge et retourne les sections config.
"""
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QTabWidget,
    QWidget,
    QLabel,
)
from PyQt6.QtCore import Qt

try:
    from core.device_detection import list_serial_ports
except ImportError:
    def list_serial_ports():
        return []


def _make_serial_form(parent, config: dict, baudrate_options: list):
    """Crée un formulaire (port, débit, timeouts, log) et retourne (widget, get_values)."""
    port_combo = QComboBox()
    port_combo.setEditable(True)
    for p in list_serial_ports():
        port_combo.addItem(p)
    port_combo.setCurrentText(config.get("port", "COM1"))

    baud_combo = QComboBox()
    for b in baudrate_options or [9600, 19200, 38400, 57600, 115200]:
        baud_combo.addItem(str(b))
    baud_combo.setCurrentText(str(config.get("baudrate", 9600)))

    timeout_spin = QDoubleSpinBox()
    timeout_spin.setRange(0.5, 30)
    timeout_spin.setValue(float(config.get("timeout", 2)))
    timeout_spin.setDecimals(1)

    write_timeout_spin = QDoubleSpinBox()
    write_timeout_spin.setRange(0.5, 30)
    write_timeout_spin.setValue(float(config.get("write_timeout", 2)))
    write_timeout_spin.setDecimals(1)

    log_check = QCheckBox()
    log_check.setChecked(bool(config.get("log_exchanges", False)))

    form = QFormLayout()
    form.addRow("Port", port_combo)
    form.addRow("Débit (bauds)", baud_combo)
    form.addRow("Timeout lecture (s)", timeout_spin)
    form.addRow("Timeout écriture (s)", write_timeout_spin)
    form.addRow("Logger les échanges", log_check)

    def get_values():
        return {
            "port": port_combo.currentText().strip(),
            "baudrate": int(baud_combo.currentText()),
            "bytesize": config.get("bytesize", 8),
            "parity": config.get("parity", "N"),
            "stopbits": config.get("stopbits", 1),
            "timeout": timeout_spin.value(),
            "write_timeout": write_timeout_spin.value(),
            "log_exchanges": log_check.isChecked(),
        }

    widget = QWidget()
    widget.setLayout(form)
    return widget, get_values


class SerialConfigDialog(QDialog):
    def __init__(self, config: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration série")
        self._config = config or {}
        baud_opts = self._config.get("limits", {}).get("baudrate_options", [9600, 19200, 38400, 57600, 115200])

        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()

        sm = self._config.get("serial_multimeter", {})
        w_m, self._get_multimeter = _make_serial_form(self, sm, baud_opts)
        self._tabs.addTab(w_m, "Multimètre")

        sg = self._config.get("serial_generator", {})
        w_g, self._get_generator = _make_serial_form(self, sg, baud_opts)
        self._tabs.addTab(w_g, "Générateur")

        layout.addWidget(self._tabs)
        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def get_updated_config(self) -> dict:
        """Retourne la config avec serial_multimeter et serial_generator mis à jour."""
        out = dict(self._config)
        out["serial_multimeter"] = self._get_multimeter()
        out["serial_generator"] = self._get_generator()
        return out
