"""
Oscilloscope HANMATEK DOS1102 : panels réutilisables et vue composée.
"""
from .oscilloscope_view import OscilloscopeView
from .connection_panel import OscilloscopeConnectionPanel
from .acquisition_trigger_panel import OscilloscopeAcqTriggerPanel
from .measurement_panel import OscilloscopeMeasurementPanel
from .waveform_panel import OscilloscopeWaveformPanel
from .channels_panel import OscilloscopeChannelsPanel

__all__ = [
    "OscilloscopeView",
    "OscilloscopeConnectionPanel",
    "OscilloscopeAcqTriggerPanel",
    "OscilloscopeMeasurementPanel",
    "OscilloscopeWaveformPanel",
    "OscilloscopeChannelsPanel",
]
