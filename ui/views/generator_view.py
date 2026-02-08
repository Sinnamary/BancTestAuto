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
from PyQt6.QtCore import QThread, pyqtSignal, Qt


class GeneratorApplyWorker(QThread):
    """Thread pour appliquer les paramètres (évite de bloquer l'UI)."""
    done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        fy6900,
        waveform: int,
        freq_hz: float,
        amp_peak: float,
        offset_v: float,
        duty_percent: float,
        phase_deg: float,
        channel: int = 1,
    ):
        super().__init__()
        self._fy6900 = fy6900
        self._waveform = waveform
        self._freq_hz = freq_hz
        self._amp_peak = amp_peak
        self._offset_v = offset_v
        self._duty_percent = duty_percent
        self._phase_deg = phase_deg
        self._channel = channel

    def run(self):
        try:
            ch = self._channel
            self._fy6900.set_waveform(self._waveform, channel=ch)
            self._fy6900.set_amplitude_peak_v(self._amp_peak, channel=ch)
            self._fy6900.set_offset_v(self._offset_v, channel=ch)
            self._fy6900.set_frequency_hz(self._freq_hz, channel=ch)
            self._fy6900.set_duty_cycle_percent(self._duty_percent, channel=ch)
            self._fy6900.set_phase_deg(self._phase_deg, channel=ch)
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

        # Style des boutons radio : indicateur plus grand et contraste fort (sélection bien visible)
        _radio_style = """
            QRadioButton {
                font-weight: 500;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #555;
                background: #fff;
            }
            QRadioButton::indicator:checked {
                background: #1565c0;
                border: 2px solid #0d47a1;
            }
            QRadioButton::indicator:hover {
                border-color: #1565c0;
            }
        """
        self.setStyleSheet(_radio_style)

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
        self._freq_spin.setToolTip("Valeur en Hz ; envoyée au générateur en µHz (14 chiffres, doc FY6900).")
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
        self._duty_spin = QDoubleSpinBox()
        self._duty_spin.setRange(0, 100)
        self._duty_spin.setValue(50)
        self._duty_spin.setDecimals(1)
        self._duty_spin.setSuffix(" %")
        self._duty_spin.setToolTip("Rapport cyclique (surtout pour forme carrée/triangle)")
        form.addRow("Rapport cyclique", self._duty_spin)
        self._phase_spin = QDoubleSpinBox()
        self._phase_spin.setRange(0, 360)
        self._phase_spin.setValue(0)
        self._phase_spin.setDecimals(1)
        self._phase_spin.setSuffix(" °")
        self._phase_spin.setToolTip("Phase en degrés (0–360)")
        form.addRow("Phase", self._phase_spin)
        layout.addWidget(form_gb)

        # État sortie par voie (lecture seule dans l'UI ; modifié par les boutons Sortie ON/OFF)
        self._output_state = {1: False, 2: False}

        out_gb = QGroupBox("Sortie")
        out_layout = QVBoxLayout(out_gb)
        out_layout.addWidget(QLabel("État des sorties (lecture seule) :"))
        row_flags = QHBoxLayout()
        self._flag_voie1 = QLabel("Voie 1 : OFF")
        self._flag_voie2 = QLabel("Voie 2 : OFF")
        for lbl in (self._flag_voie1, self._flag_voie2):
            lbl.setStyleSheet(
                "padding: 6px 12px; border-radius: 4px; font-weight: 600; min-width: 90px;"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_output_flags()
        row_flags.addWidget(self._flag_voie1)
        row_flags.addWidget(self._flag_voie2)
        row_flags.addStretch()
        out_layout.addLayout(row_flags)
        out_layout.addWidget(QLabel("Les boutons « Sortie ON » et « Sortie OFF » ci‑dessous agissent sur la voie sélectionnée ci‑dessus."))
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
        # Mapping UI (Sinusoïde, Triangle, Carré, Dent de scie) → codes FY6900 (0=SINE, 7=TRGL, 1=Square, 8=Ramp)
        WAVEFORM_CODES = (0, 7, 1, 8)
        waveform = WAVEFORM_CODES[self._waveform_combo.currentIndex()]
        freq = self._freq_spin.value()
        amp = self._amplitude_spin.value()
        offset = self._offset_spin.value()
        duty = self._duty_spin.value()
        phase = self._phase_spin.value()
        channel = self.get_selected_channel()
        self._apply_btn.setEnabled(False)
        self._worker = GeneratorApplyWorker(
            self._fy6900, waveform, freq, amp, offset, duty, phase, channel
        )
        self._worker.done.connect(self._on_apply_done)
        self._worker.error.connect(self._on_apply_error)
        self._worker.finished.connect(lambda: self._apply_btn.setEnabled(True))
        self._worker.start()

    def _on_apply_done(self):
        pass  # optionnel : message status bar

    def _on_apply_error(self, msg: str):
        QMessageBox.warning(self, "Générateur", f"Erreur : {msg}")

    def _update_output_flags(self):
        """Met à jour les indicateurs Voie 1 / Voie 2 (couleur et texte, lecture seule)."""
        for ch, lbl in ((1, self._flag_voie1), (2, self._flag_voie2)):
            on = self._output_state[ch]
            text = "Voie {} : ON".format(ch) if on else "Voie {} : OFF".format(ch)
            lbl.setText(text)
            if on:
                lbl.setStyleSheet(
                    "padding: 6px 12px; border-radius: 4px; font-weight: 600; min-width: 90px;"
                    " background-color: #2e7d32; color: white;"
                )
            else:
                lbl.setStyleSheet(
                    "padding: 6px 12px; border-radius: 4px; font-weight: 600; min-width: 90px;"
                    " background-color: #616161; color: white;"
                )

    def _on_output_on(self):
        if not self._fy6900:
            return
        ch = self.get_selected_channel()
        try:
            self._fy6900.set_output(True, channel=ch)
            self._output_state[ch] = True
            self._update_output_flags()
        except Exception as e:
            QMessageBox.warning(self, "Générateur", str(e))

    def _on_output_off(self):
        if not self._fy6900:
            return
        ch = self.get_selected_channel()
        try:
            self._fy6900.set_output(False, channel=ch)
            self._output_state[ch] = False
            self._update_output_flags()
        except Exception as e:
            QMessageBox.warning(self, "Générateur", str(e))

    def get_selected_channel(self) -> int:
        return 2 if self._channel_2.isChecked() else 1
