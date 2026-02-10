"""
Constantes SCPI pour l'oscilloscope HANMATEK DOS1102.
Syntaxe documentée par le forum NI et le manuel DSO2000 (Hantek).
"""
# Identification
IDN = "*IDN?"
RST = "*RST"

# Acquisition
ACQ_MODE_SAMP = ":ACQ:MODE SAMP"
ACQ_MODE_PEAK = ":ACQ:MODE PEAK"
ACQ_MODE_AVE = ":ACQ:MODE AVE"

# Couplage canal (CH1 / CH2)
def CH_COUP(ch: int, mode: str):  # noqa: N802
    """Couplage : DC, AC, GND."""
    return f":CH{ch}:COUP {mode}"

CH1_COUP_DC = ":CH1:COUP DC"
CH1_COUP_AC = ":CH1:COUP AC"
CH1_COUP_GND = ":CH1:COUP GND"
CH2_COUP_DC = ":CH2:COUP DC"
CH2_COUP_AC = ":CH2:COUP AC"
CH2_COUP_GND = ":CH2:COUP GND"

# Échelle / position / offset canal
def CH_SCA(ch: int, value):  # noqa: N802
    return f":CH{ch}:SCA {value}"

def CH_POS(ch: int, value):  # noqa: N802
    return f":CH{ch}:POS {value}"

def CH_OFFS(ch: int, value):  # noqa: N802
    return f":CH{ch}:OFFS {value}"

# Sonde (1X, 10X, 100X, 1000X)
def CH_PROBE(ch: int, value: str):  # noqa: N802
    return f":CH{ch}:PROBE {value}"

# Inversion
def CH_INV(ch: int, state: str):  # noqa: N802
    """state: OFF ou ON."""
    return f":CH{ch}:INV {state}"

# Base de temps (horizontal)
def HOR_OFFS(value):  # noqa: N802
    return f":HOR:OFFS {value}"

def HOR_SCAL(value):  # noqa: N802
    return f":HOR:SCAL {value}"

# Trigger
TRIG_EDGE = ":TRIG EDGE"
TRIG_VIDEO = ":TRIG VIDEO"
TRIG_TYPE_SING = ":TRIG:TYPE SING"
TRIG_TYPE_ALT = ":TRIG:TYPE ALT"

# Mesures — requêtes générales
MEAS_QUERY = ":MEAS?"

# Mesures par canal (CH1 ou CH2) et type (tuple pour compatibilité)
# Version nettoyée : uniquement les types qui répondent de manière fiable
# sur le DOS1102 (cf. tests via tools.dos1102_cli --scan-meas).
MEAS_TYPES = (
    "PERiod",
    "FREQuency",
    "AVERage",
    "PKPK",
    "MAX",
    "MIN",
    "VTOP",
    "VBASe",
    "VAMP",
    "PREShoot",
    "RTime",
    "FTime",
    "PWIDth",
    "NWIDth",
    "PDUTy",
    "NDUTy",
    "RDELay",
    "FDELay",
    "CYCRms",
    "RISEPHASEDELAY",
)

# Liste (libellé, type SCPI) pour toutes les mesures utilisables sur une voie (CH1 ou CH2)
# Nettoyée pour exclure les commandes qui ne renvoient rien (timeouts).
MEAS_TYPES_PER_CHANNEL = (
    ("Période", "PERiod"),
    ("Fréquence", "FREQuency"),
    ("Moyenne", "AVERage"),
    ("Crête à crête", "PKPK"),
    ("Max", "MAX"),
    ("Min", "MIN"),
    ("Sommet", "VTOP"),
    ("Base", "VBASe"),
    ("Amplitude", "VAMP"),
    ("PREShoot", "PREShoot"),
    ("Temps montée", "RTime"),
    ("Temps descente", "FTime"),
    ("Largeur imp. +", "PWIDth"),
    ("Largeur imp. -", "NWIDth"),
    ("Rapport cyclique +", "PDUTy"),
    ("Rapport cyclique -", "NDUTy"),
    ("Délai montée (vs réf)", "RDELay"),
    ("Délai descente (vs réf)", "FDELay"),
    ("CYCRms", "CYCRms"),
    ("Délai phase montée (vs réf)", "RISEPHASEDELAY"),
)

# Mesures inter-canal : délai de CH2 par rapport à CH1 (à requêter sur CH2)
MEAS_TYPES_INTER_CHANNEL = (
    ("Délai phase montée (CH2 vs CH1)", "RISEPHASEDELAY"),
    ("Délai montée (CH2 vs CH1)", "RDELay"),
    ("Délai descente (CH2 vs CH1)", "FDELay"),
)

# Forme d'onde — données de courbe (DSO2000 : :WAVeform:DATA:ALL? ; syntaxe courte possible)
WAVEFORM_DATA_ALL = ":WAV:DATA:ALL?"
WAVEFORM_DATA_ALL_LONG = ":WAVeform:DATA:ALL?"


def MEAS_CH_QUERY(ch: int, meas_type: str):  # noqa: N802
    """Ex. MEAS_CH_QUERY(1, 'FREQuency') -> :MEAS:CH1:FREQuency?"""
    return f":MEAS:CH{ch}:{meas_type}?"
