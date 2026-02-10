"""
Vue maquette « Oscilloscope DOS1102 ».

Objectif : représenter l'ensemble des grands blocs de paramètres disponibles
sur l'oscilloscope (connexion, acquisition, trigger, mesures, forme d'onde,
canaux, etc.) sans implémenter la logique de communication réelle.

Cette vue ne dépend pas de core/ et ne crée aucune connexion physique.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QPlainTextEdit,
)


class OscilloscopeView(QWidget):
    """
    Maquette de l'onglet « Oscilloscope ».

    Les contrôles sont interactifs (listes déroulantes, champs numériques),
    mais aucun bouton n'envoie de commande à un appareil réel : tous les
    boutons d'action sont volontairement désactivés.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(12)

        # Ordre des blocs : d'abord les réglages les plus utilisés (base de temps,
        # trigger, canaux), puis les fonctions plus ponctuelles (mesures, forme
        # d'onde, infos).
        content_layout.addWidget(self._build_connection_group())
        content_layout.addWidget(self._build_acquisition_trigger_group())
        content_layout.addWidget(self._build_channels_group())
        content_layout.addWidget(self._build_measurements_group())
        content_layout.addWidget(self._build_waveform_group())
        content_layout.addWidget(self._build_info_group())
        content_layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Sous-blocs
    # ------------------------------------------------------------------
    def _build_connection_group(self) -> QGroupBox:
        gb = QGroupBox("Connexion (maquette)")
        layout = QHBoxLayout(gb)

        layout.addWidget(QLabel("Mode :"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Série (COM)", "USB (WinUSB/PyUSB)"])
        layout.addWidget(self._mode_combo)

        layout.addWidget(QLabel("Port série :"))
        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        self._port_combo.setMinimumWidth(120)
        self._port_combo.setPlaceholderText("COM3, /dev/ttyUSB0, ...")
        layout.addWidget(self._port_combo)

        self._speed_label = QLabel("Vitesse : 115200 bauds")
        layout.addWidget(self._speed_label)

        layout.addWidget(QLabel("USB :"))
        self._usb_combo = QComboBox()
        self._usb_combo.setMinimumWidth(220)
        self._usb_combo.setPlaceholderText("Liste des périphériques USB (maquette)")
        layout.addWidget(self._usb_combo)

        self._connect_btn = QPushButton("Connexion")
        self._connect_btn.setEnabled(False)
        layout.addWidget(self._connect_btn)

        layout.addStretch()
        return gb

    def _build_acquisition_trigger_group(self) -> QGroupBox:
        gb = QGroupBox("Acquisition et Trigger")
        layout = QHBoxLayout(gb)

        # Acquisition
        acq_gb = QGroupBox("Acquisition")
        acq_layout = QFormLayout(acq_gb)
        self._acq_mode_combo = QComboBox()
        self._acq_mode_combo.addItems(
            [
                "SAMP (échantillonnage)",
                "PEAK (pic)",
                "AVE (moyenne)",
            ]
        )
        acq_layout.addRow("Mode :", self._acq_mode_combo)
        self._timebase_spin = QDoubleSpinBox()
        self._timebase_spin.setDecimals(6)
        self._timebase_spin.setMinimum(1e-9)
        self._timebase_spin.setMaximum(1000.0)
        self._timebase_spin.setValue(1e-3)
        self._timebase_spin.setSuffix(" s/div")
        acq_layout.addRow("Base de temps :", self._timebase_spin)
        self._acq_apply_btn = QPushButton("Appliquer acquisition")
        self._acq_apply_btn.setEnabled(False)
        acq_layout.addRow("", self._acq_apply_btn)

        # Trigger
        trig_gb = QGroupBox("Trigger")
        trig_layout = QFormLayout(trig_gb)
        self._trig_type_combo = QComboBox()
        self._trig_type_combo.addItems(["EDGE", "VIDEO"])
        trig_layout.addRow("Type :", self._trig_type_combo)
        self._trig_source_combo = QComboBox()
        self._trig_source_combo.addItems(["CH1", "CH2", "Ext", "Line"])
        trig_layout.addRow("Source :", self._trig_source_combo)
        self._trig_level_spin = QDoubleSpinBox()
        self._trig_level_spin.setSuffix(" V")
        self._trig_level_spin.setMinimum(-1000.0)
        self._trig_level_spin.setMaximum(1000.0)
        self._trig_level_spin.setSingleStep(0.1)
        trig_layout.addRow("Niveau :", self._trig_level_spin)
        self._trig_apply_btn = QPushButton("Appliquer trigger")
        self._trig_apply_btn.setEnabled(False)
        trig_layout.addRow("", self._trig_apply_btn)

        layout.addWidget(acq_gb)
        layout.addWidget(trig_gb)
        return gb

    def _build_measurements_group(self) -> QGroupBox:
        gb = QGroupBox("Mesures")
        layout = QVBoxLayout(gb)

        # Mesures par voie : organisation similaire aux canaux (CH1 / CH2 côte à côte)
        per_channel_row = QHBoxLayout()
        per_channel_row.setSpacing(16)

        def _add_measure_types(combo: QComboBox) -> None:
            # Liste issue de core.dos1102_commands.MEAS_TYPES_PER_CHANNEL (dupliquée en maquette)
            for label in [
                "Période",
                "Fréquence",
                "Moyenne",
                "Crête à crête",
                "SQUARESUM",
                "Max",
                "Min",
                "Sommet",
                "Base",
                "Amplitude",
                "VPRESHOOT",
                "PREShoot",
                "Temps montée",
                "Temps descente",
                "Largeur imp. +",
                "Largeur imp. -",
                "Rapport cyclique +",
                "Rapport cyclique -",
                "Délai montée (vs réf)",
                "Délai descente (vs réf)",
                "RMS",
                "CYCRms",
                "WORKPERIOD",
                "Délai phase montée (vs réf)",
                "PPULSENUM",
                "NPULSENUM",
                "RISINGEDGENUM",
                "FALLINGEDGENUM",
                "AREA",
                "CYCLEAREA",
            ]:
                combo.addItem(label)

        # Voie 1
        ch1_gb = QGroupBox("Voie 1 (CH1)")
        ch1_layout = QFormLayout(ch1_gb)
        ch1_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._meas_ch1_type_combo = QComboBox()
        _add_measure_types(self._meas_ch1_type_combo)
        ch1_layout.addRow("Type de mesure :", self._meas_ch1_type_combo)
        self._meas_ch1_btn = QPushButton("Mesure CH1")
        self._meas_ch1_btn.setEnabled(False)
        ch1_layout.addRow("", self._meas_ch1_btn)
        self._meas_ch1_result = QLabel("—")
        ch1_layout.addRow("Résultat :", self._meas_ch1_result)
        per_channel_row.addWidget(ch1_gb)

        # Voie 2
        ch2_gb = QGroupBox("Voie 2 (CH2)")
        ch2_layout = QFormLayout(ch2_gb)
        ch2_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._meas_ch2_type_combo = QComboBox()
        _add_measure_types(self._meas_ch2_type_combo)
        ch2_layout.addRow("Type de mesure :", self._meas_ch2_type_combo)
        self._meas_ch2_btn = QPushButton("Mesure CH2")
        self._meas_ch2_btn.setEnabled(False)
        ch2_layout.addRow("", self._meas_ch2_btn)
        self._meas_ch2_result = QLabel("—")
        ch2_layout.addRow("Résultat :", self._meas_ch2_result)
        per_channel_row.addWidget(ch2_gb)

        layout.addLayout(per_channel_row)

        # Mesure générale
        general_gb = QGroupBox("Mesure générale (:MEAS?)")
        gen_layout = QFormLayout(general_gb)
        self._meas_general_label = QLabel("—")
        gen_layout.addRow("Résultat :", self._meas_general_label)
        self._meas_general_btn = QPushButton("Mesure générale")
        self._meas_general_btn.setEnabled(False)
        gen_layout.addRow("", self._meas_general_btn)
        layout.addWidget(general_gb)

        # Mesures complètes (Bode, etc.)
        all_gb = QGroupBox("Toutes les mesures (Bode phase, etc.)")
        all_layout = QVBoxLayout(all_gb)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Source :"))
        self._meas_all_combo = QComboBox()
        self._meas_all_combo.addItems(
            [
                "Voie 1 (CH1)",
                "Voie 2 (CH2)",
                "Inter-canal (CH2 vs CH1)",
            ]
        )
        top_row.addWidget(self._meas_all_combo)
        self._meas_all_btn = QPushButton("Lire toutes les mesures")
        self._meas_all_btn.setEnabled(False)
        top_row.addWidget(self._meas_all_btn)
        top_row.addStretch()
        all_layout.addLayout(top_row)

        self._meas_all_text = QPlainTextEdit()
        self._meas_all_text.setReadOnly(True)
        self._meas_all_text.setMaximumHeight(160)
        self._meas_all_text.setPlaceholderText(
            "Zone de texte pour afficher la liste des mesures calculées par l'oscilloscope.\n"
            "(maquette : aucun appel à l'appareil réel)"
        )
        all_layout.addWidget(self._meas_all_text)

        layout.addWidget(all_gb)
        return gb

    def _build_waveform_group(self) -> QGroupBox:
        gb = QGroupBox("Forme d'onde")
        layout = QVBoxLayout(gb)

        row = QHBoxLayout()
        self._wave_fetch_btn = QPushButton("Récupérer forme d'onde (:WAV:DATA:ALL?)")
        self._wave_fetch_btn.setEnabled(False)
        row.addWidget(self._wave_fetch_btn)
        self._wave_plot_btn = QPushButton("Afficher courbe")
        self._wave_plot_btn.setEnabled(False)
        row.addWidget(self._wave_plot_btn)
        row.addStretch()
        layout.addLayout(row)

        self._wave_text = QPlainTextEdit()
        self._wave_text.setReadOnly(True)
        self._wave_text.setMaximumHeight(140)
        self._wave_text.setPlaceholderText(
            "Résumé ou données brutes de la forme d'onde.\n"
            "(maquette : les boutons sont désactivés, aucun téléchargement réel)"
        )
        layout.addWidget(self._wave_text)

        return gb

    def _build_channels_group(self) -> QGroupBox:
        gb = QGroupBox("Canaux")
        layout = QHBoxLayout(gb)
        layout.setSpacing(16)

        # Voie 1 - bloc vertical rappelant les commandes physiques
        ch1 = QGroupBox("Voie 1 (CH1)")
        ch1_form = QFormLayout(ch1)
        ch1_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._ch1_enable = QCheckBox("Activer CH1")
        self._ch1_enable.setChecked(True)
        ch1_form.addRow("", self._ch1_enable)

        self._ch1_coupling = QComboBox()
        self._ch1_coupling.addItems(["DC", "AC", "GND"])
        ch1_form.addRow("Couplage :", self._ch1_coupling)

        self._ch1_scale = QDoubleSpinBox()
        self._ch1_scale.setSuffix(" V/div")
        self._ch1_scale.setMinimum(1e-3)
        self._ch1_scale.setMaximum(1000.0)
        self._ch1_scale.setValue(1.0)
        ch1_form.addRow("Échelle :", self._ch1_scale)

        self._ch1_position = QDoubleSpinBox()
        self._ch1_position.setSuffix(" div")
        self._ch1_position.setMinimum(-10.0)
        self._ch1_position.setMaximum(10.0)
        ch1_form.addRow("Position :", self._ch1_position)

        self._ch1_offset = QSpinBox()
        self._ch1_offset.setSuffix(" mV")
        self._ch1_offset.setRange(-100000, 100000)
        ch1_form.addRow("Offset :", self._ch1_offset)

        self._ch1_invert = QCheckBox("Inverser")
        ch1_form.addRow("", self._ch1_invert)

        layout.addWidget(ch1)

        # Voie 2 - même organisation verticale pour rester lisible
        ch2 = QGroupBox("Voie 2 (CH2)")
        ch2_form = QFormLayout(ch2)
        ch2_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._ch2_enable = QCheckBox("Activer CH2")
        self._ch2_enable.setChecked(True)
        ch2_form.addRow("", self._ch2_enable)

        self._ch2_coupling = QComboBox()
        self._ch2_coupling.addItems(["DC", "AC", "GND"])
        ch2_form.addRow("Couplage :", self._ch2_coupling)

        self._ch2_scale = QDoubleSpinBox()
        self._ch2_scale.setSuffix(" V/div")
        self._ch2_scale.setMinimum(1e-3)
        self._ch2_scale.setMaximum(1000.0)
        self._ch2_scale.setValue(1.0)
        ch2_form.addRow("Échelle :", self._ch2_scale)

        self._ch2_position = QDoubleSpinBox()
        self._ch2_position.setSuffix(" div")
        self._ch2_position.setMinimum(-10.0)
        self._ch2_position.setMaximum(10.0)
        ch2_form.addRow("Position :", self._ch2_position)

        self._ch2_offset = QSpinBox()
        self._ch2_offset.setSuffix(" mV")
        self._ch2_offset.setRange(-100000, 100000)
        ch2_form.addRow("Offset :", self._ch2_offset)

        self._ch2_invert = QCheckBox("Inverser")
        ch2_form.addRow("", self._ch2_invert)

        layout.addWidget(ch2)

        # Colonne de commandes générales pour les deux voies (style boutons physiques)
        commands = QGroupBox("Commandes")
        commands_layout = QVBoxLayout(commands)
        commands_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._channels_apply_btn = QPushButton("Appliquer canaux")
        self._channels_apply_btn.setEnabled(False)
        commands_layout.addWidget(self._channels_apply_btn)

        self._channels_auto_btn = QPushButton("Auto scale (maquette)")
        self._channels_auto_btn.setEnabled(False)
        commands_layout.addWidget(self._channels_auto_btn)

        self._channels_copy_btn = QPushButton("Copier CH1→CH2")
        self._channels_copy_btn.setEnabled(False)
        commands_layout.addWidget(self._channels_copy_btn)

        commands_layout.addStretch()
        layout.addWidget(commands)

        return gb

    def _build_info_group(self) -> QGroupBox:
        gb = QGroupBox("Informations maquette")
        layout = QVBoxLayout(gb)
        label = QLabel(
            "Cette vue concentre les principaux paramètres de l'oscilloscope :\n"
            "- connexion (série / USB et ports),\n"
            "- modes d'acquisition et de trigger,\n"
            "- mesures (simples et complètes),\n"
            "- récupération de forme d'onde,\n"
            "- réglages par canal (couplage, échelle).\n\n"
            "Tous les boutons d'action sont volontairement désactivés pour l'instant.\n"
            "L'implémentation réelle branchera ces contrôles sur le protocole DOS1102."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        return gb

