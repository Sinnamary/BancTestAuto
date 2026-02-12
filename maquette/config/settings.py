"""
Stub config pour la maquette : pas de lecture/écriture fichier, retourne des dict par défaut.
"""
from pathlib import Path
from typing import Any

from core.app_paths import get_config_path

DEFAULT_CONFIG_PATH = get_config_path()

DEFAULTS = {
    "serial_multimeter": {"port": "COM3", "baudrate": 9600},
    "serial_generator": {"port": "COM4", "baudrate": 115200},
    "usb_oscilloscope": {"vendor_id": 0x5345, "product_id": 0x1234},
    "serial_power_supply": {"port": "COM6", "baudrate": 9600},
    "measurement": {"default_rate": "F", "default_auto_range": True, "refresh_interval_ms": 500},
    "display": {"font_size": "large", "font_family": "Segoe UI", "theme": "dark", "secondary_display": False},
    "limits": {"history_size": 100, "baudrate_options": [9600, 19200, 38400, 57600, 115200]},
    "logging": {"output_dir": "./logs", "level": "INFO", "default_interval_s": 5, "default_duration_min": 60, "duration_unlimited": False},
    "generator": {"default_channel": 1, "waveform": 0, "frequency_hz": 1000, "amplitude_v_peak": 1.414, "offset_v": 0},
    "filter_test": {"generator_channel": 1, "f_min_hz": 10, "f_max_hz": 100000, "points_per_decade": 10, "scale": "log", "settling_ms": 200, "ue_rms": 1.0, "measure_source": "multimeter", "oscillo_channel_ue": 1, "oscillo_channel_us": 2, "phase_skip_below_scale_ch2_mv": 20},
    "bode_viewer": {"plot_background_dark": True, "curve_color": "#e0c040", "grid_visible": True},
}


def get_config_file_path(path: Path | str | None = None) -> Path:
    if path is not None:
        return Path(path) if isinstance(path, str) else path
    return DEFAULT_CONFIG_PATH


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """En maquette : retourne toujours les valeurs par défaut (pas de fichier)."""
    return dict(DEFAULTS)


def save_config(config: dict[str, Any], path: Path | str | None = None) -> None:
    """En maquette : no-op."""
    pass


def get_serial_multimeter_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("serial_multimeter", DEFAULTS["serial_multimeter"]).copy()


def get_serial_generator_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("serial_generator", DEFAULTS["serial_generator"]).copy()


def get_usb_oscilloscope_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("usb_oscilloscope", DEFAULTS["usb_oscilloscope"]).copy()


def get_serial_power_supply_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("serial_power_supply", DEFAULTS["serial_power_supply"]).copy()


def get_filter_test_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("filter_test", DEFAULTS["filter_test"]).copy()


def get_generator_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("generator", DEFAULTS["generator"]).copy()


def get_logging_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("logging", DEFAULTS["logging"]).copy()


def get_bode_viewer_config(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("bode_viewer", DEFAULTS["bode_viewer"]).copy()
