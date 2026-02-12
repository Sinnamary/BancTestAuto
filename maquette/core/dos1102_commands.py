"""
Stub constantes SCPI oscilloscope DOS1102 pour la maquette.
"""
IDN = "*IDN?"
RST = "*RST"
MEAS_QUERY = ":MEAS?"

MEAS_TYPES_PER_CHANNEL = (
    ("Période", "PERiod"),
    ("Fréquence", "FREQuency"),
    ("Moyenne", "AVERage"),
    ("Crête à crête", "PKPK"),
    ("Max", "MAX"),
    ("Min", "MIN"),
)

MEAS_TYPES_INTER_CHANNEL = (
    ("Délai phase montée (CH2 vs CH1)", "RISEPHASEDELAY"),
    ("Délai montée (CH2 vs CH1)", "RDELay"),
    ("Délai descente (CH2 vs CH1)", "FDELay"),
)

WAVEFORM_HEAD = ":DATA:WAVE:SCREen:HEAD?"

def WAVEFORM_SCREEN_CH(ch: int):
    return f":DATA:WAVE:SCREEN:CH{ch}?"

def MEAS_CH_QUERY(ch: int, meas_type: str):
    return f":MEAS:CH{ch}:{meas_type}?"

def CH_COUP(ch: int, mode: str):
    return f":CH{ch}:COUP {mode}"

def _ch_scal_to_scope_format(v_per_div: float) -> str:
    v = float(v_per_div)
    if v < 1.0:
        mv = v * 1000.0
        return f"{int(mv)}mV" if abs(mv - round(mv)) < 1e-6 else f"{mv}mV"
    return f"{int(v)}V" if abs(v - round(v)) < 1e-6 else f"{v}V"


def CH_SCA(ch: int, value):
    val = _ch_scal_to_scope_format(value) if isinstance(value, (int, float)) else value
    return f":CH{ch}:SCAL {val}"

def CH_POS(ch: int, value):
    return f":CH{ch}:POS {value}"

def CH_OFFS(ch: int, value):
    return f":CH{ch}:OFFS {value}"

def CH_PROBE(ch: int, value: str):
    return f":CH{ch}:PROBE {value}"

def CH_INV(ch: int, state: str):
    return f":CH{ch}:INV {state}"

def HOR_OFFS(value):
    return f":HOR:OFFS {value}"

def HOR_SCAL(value):
    return f":HOR:SCAL {value}"

CH1_COUP_DC = ":CH1:COUP DC"
CH1_COUP_AC = ":CH1:COUP AC"
CH1_COUP_GND = ":CH1:COUP GND"
CH2_COUP_DC = ":CH2:COUP DC"
CH2_COUP_AC = ":CH2:COUP AC"
CH2_COUP_GND = ":CH2:COUP GND"
ACQ_MODE_SAMP = ":ACQ:MODE SAMP"
ACQ_MODE_PEAK = ":ACQ:MODE PEAK"
ACQ_MODE_AVE = ":ACQ:MODE AVE"
TRIG_EDGE = ":TRIG EDGE"
TRIG_VIDEO = ":TRIG VIDEO"
TRIG_TYPE_SING = ":TRIG:TYPE SING"
TRIG_TYPE_ALT = ":TRIG:TYPE ALT"
WAVEFORM_DATA_ALL = ":WAV:DATA:ALL?"
WAVEFORM_DATA_ALL_LONG = ":WAVeform:DATA:ALL?"
MEAS_TYPES = ("PERiod", "FREQuency", "AVERage", "PKPK", "MAX", "MIN")
