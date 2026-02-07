"""
Vue onglet Générateur FY6900 — Voie 1/2, forme, fréquence, amplitude, offset, sortie.
Connectée à core.Fy6900Protocol pour appliquer les paramètres et ON/OFF.
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QRadioButton,
    QButtonGroup,
    QFormLayout,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal


class GeneratorApplyWorker(QThread):
    """Thread pour appliquer les paramètres (évite de bloquer l'UI)."""
    done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, fy6900, waveform: int, freq_hz: float, amp_peak: float, offset_v: float):
        super().__init__()
        self._fy6900 = fy6900
        self._waveform = waveform
        self._freq_hz = freq_hz
        self._amp_peak = amp_peak
        self._offset_v = offset_v

    def run(self):
        try:
            self._fy6900.set_waveform(self._waveform)
            self._fy6900.set_frequency_hz(self._freq_hz)
            self._fy6900.set_amplitude_peak_v(self._amp_peak)
            self._fy6900.set_offset_v(self._offset_v)
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))


class GeneratorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fy6900 = None
        self._build_ui()

    def set_fy6900(self, fy6900):
        """Injection du protocole FY6900 (depuis main_window)."""
        self._fy6900 = fy6900

    def _build_ui(self):
        layout = QVBoxLayout(self)

        channel_gb = QGroupBox("Voie")
        channel_layout = QHBoxLayout(channel_gb)
        self._channel_group = QButtonGroup(self)
        self._channel_1 = QRadioButton("Voie 1")
        self._channel_2 = QRadioButton("Voie 2")
        self._channel_1.setChecked(True)
        self._channel_group.addButton(self._channel_1)
        self._channel_group.addButton(self._channel_2)
        channel_layout.addWidget(self._channel_1)
        channel_layout.addWidget(self._channel_2)
        channel_layout.addWidget(QLabel("(paramètres appliqués à la voie choisie)"))
        channel_layout.addStretch()
        layout.addWidget(channel_gb)

        form_gb = QGroupBox("Paramètres générateur")
        form = QFormLayout(form_gb)
        self._waveform_combo = QComboBox()
        self._waveform_combo.addItems(["Sinusoïde", "Triangle", "Carré", "Dent de scie"])
        form.addRow("Forme d'onde", self._waveform_combo)
        self._freq_spin = QDoubleSpinBox()
        self._freq_spin.setRange(0.1, 20e6)
        self._freq_spin.setValue(1000)
        self._freq_spin.setDecimals(2)
        form.addRow("Fréquence (Hz)", self._freq_spin)
        self._amplitude_spin = QDoubleSpinBox()
        self._amplitude_spin.setRange(0.01, 20)
        self._amplitude_spin.setValue(1.414)
        self._amplitude_spin.setDecimals(3)
        form.addRow("Amplitude (V crête)", self._amplitude_spin)
        self._offset_spin = QDoubleSpinBox()
        self._offset_spin.setRange(-20, 20)
        self._offset_spin.setValue(0)
        self._offset_spin.setDecimals(2)
        form.addRow("Offset (V)", self._offset_spin)
        layout.addWidget(form_gb)

        out_gb = QGroupBox("Sortie")
        out_layout = QHBoxLayout(out_gb)
        out_layout.addWidget(QLabel("Sortie de la voie sélectionnée :"))
        self._out_off = QRadioButton("OFF")
        self._out_on = QRadioButton("ON")
        self._out_off.setChecked(True)
        out_layout.addWidget(self._out_off)
        out_layout.addWidget(self._out_on)
        layout.addWidget(out_gb)

        btns = QHBoxLayout()
        self._apply_btn = QPushButton("Appliquer")
        self._apply_btn.clicked.connect(self._on_apply)
        self._on_btn = QPushButton("Sortie ON")
        self._on_btn.clicked.connect(self._on_output_on)
        self._off_btn = QPushButton("Sortie OFF")
        self._off_btn.clicked.connect(self._on_output_off)
        btns.addWidget(self._apply_btn)
        btns.addWidget(self._on_btn)
        btns.addWidget(self._off_btn)
        layout.addLayout(btns)
        layout.addStretch()

    def _on_apply(self):
        if not self._fy6900:
            QMessageBox.warning(self, "Générateur", "Connexion générateur requise.")
            return
        waveform = self._waveform_combo.currentIndex()  # 0 = sinusoïde (WMW0)
        freq = self._freq_spin.value()
        amp = self._amplitude_spin.value()
        offset = self._offset_spin.value()
        self._apply_btn.setEnabled(False)
        self._worker = GeneratorApplyWorker(self._fy6900, waveform, freq, amp, offset)
        self._worker.done.connect(self._on_apply_done)
        self._worker.error.connect(self._on_apply_error)
        self._worker.finished.connect(lambda: self._apply_btn.setEnabled(True))
        self._worker.start()

    def _on_apply_done(self):
        pass  # optionnel : message status bar

    def _on_apply_error(self, msg: str):
        QMessageBox.warning(self, "Générateur", f"Erreur : {msg}")

    def _on_output_on(self):
        if not self._fy6900:
            return
        try:
            self._fy6900.set_output(True)
            self._out_on.setChecked(True)
        except Exception as e:
            QMessageBox.warning(self, "Générateur", str(e))

    def _on_output_off(self):
        if not self._fy6900:
            return
        try:
            self._fy6900.set_output(False)
            self._out_off.setChecked(True)
        except Exception as e:
            QMessageBox.warning(self, "Générateur", str(e))

    def get_selected_channel(self) -> int:
        return 2 if self._channel_2.isChecked() else 1
