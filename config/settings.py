"""
Chargement et sauvegarde de la configuration (config.json).
Valeurs par défaut si une clé manque ; le JSON prime lorsqu'il est présent.
Compatible exécutable PyInstaller : config.json à côté du .exe.
"""
import json
from pathlib import Path
from typing import Any

from core.app_paths import get_config_path

# Emplacement du fichier de configuration (à côté du .exe en mode frozen)
DEFAULT_CONFIG_PATH = get_config_path()

# Valeurs par défaut complètes (si clé absente du JSON)
DEFAULTS = {
    "serial_multimeter": {
        "port": "COM3",
        "baudrate": 9600,
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "timeout": 2.0,
        "write_timeout": 2.0,
        "log_exchanges": False,
    },
    "serial_generator": {
        "port": "COM4",
        "baudrate": 115200,
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "timeout": 2.0,
        "write_timeout": 2.0,
        "log_exchanges": False,
    },
    "serial_oscilloscope": {
        "port": "COM5",
        "baudrate": 115200,
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "timeout": 2.0,
        "write_timeout": 2.0,
        "log_exchanges": False,
    },
    "measurement": {
        "default_rate": "F",
        "default_auto_range": True,
        "refresh_interval_ms": 500,
    },
    "display": {
        "font_size": "large",
        "font_family": "Segoe UI",
        "theme": "dark",
        "secondary_display": False,
    },
    "limits": {
        "history_size": 100,
        "baudrate_options": [9600, 19200, 38400, 57600, 115200],
    },
    "logging": {
        "output_dir": "./logs",
        "level": "INFO",
        "default_interval_s": 5,
        "default_duration_min": 60,
        "duration_unlimited": False,
    },
    "generator": {
        "default_channel": 1,
        "waveform": 0,
        "frequency_hz": 1000,
        "amplitude_v_peak": 1.414,
        "offset_v": 0,
    },
    "filter_test": {
        "generator_channel": 1,
        "f_min_hz": 10,
        "f_max_hz": 100000,
        "points_per_decade": 10,
        "scale": "log",
        "settling_ms": 200,
        "ue_rms": 1.0,
    },
    "bode_viewer": {
        "plot_background_dark": True,
        "curve_color": "#e0c040",
        "grid_visible": True,
        "grid_minor_visible": False,
        "smooth_window": 0,
        "show_raw_curve": False,
        "smooth_savgol": False,
        "y_linear": False,
        "peaks_visible": False,
    },
}


def _deep_merge(default: dict, loaded: dict) -> dict:
    """Fusionne loaded dans default (loaded prime). Pas de fusion récursive des listes."""
    out = dict(default)
    for key, value in loaded.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _resolve_config_path(path: Path | str | None) -> Path:
    """Retourne le chemin du fichier config à utiliser (avec repli si le défaut n'existe pas)."""
    if path is not None:
        return Path(path).resolve()
    p = DEFAULT_CONFIG_PATH
    if p.exists():
        return p
    # Repli : config/config.json depuis le répertoire de travail (si exécution depuis une autre racine)
    fallback = Path.cwd() / "config" / "config.json"
    if fallback.exists():
        return fallback
    return DEFAULT_CONFIG_PATH  # pour message d'erreur cohérent


def get_config_file_path(path: Path | str | None = None) -> Path:
    """Retourne le chemin du fichier config qui sera ou a été utilisé (pour affichage)."""
    return _resolve_config_path(path)


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """
    Charge la configuration depuis le fichier JSON.
    Si une section ou clé manque, utilise les valeurs par défaut.
    Essaie DEFAULT_CONFIG_PATH puis, s'il n'existe pas, cwd/config/config.json.
    """
    p = _resolve_config_path(path)
    if not p.exists():
        return dict(DEFAULTS)

    with open(p, encoding="utf-8") as f:
        loaded = json.load(f)

    return _deep_merge(dict(DEFAULTS), loaded)


def save_config(config: dict[str, Any], path: Path | str | None = None) -> None:
    """Sauvegarde la configuration dans le fichier JSON."""
    path = path or DEFAULT_CONFIG_PATH
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_serial_multimeter_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section serial_multimeter (pour la classe série multimètre)."""
    return config.get("serial_multimeter", DEFAULTS["serial_multimeter"]).copy()


def get_serial_generator_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section serial_generator (pour la classe série générateur)."""
    return config.get("serial_generator", DEFAULTS["serial_generator"]).copy()


def get_serial_oscilloscope_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section serial_oscilloscope (pour l'oscilloscope HANMATEK DOS1102)."""
    return config.get("serial_oscilloscope", DEFAULTS["serial_oscilloscope"]).copy()


def get_filter_test_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section filter_test (banc filtre)."""
    return config.get("filter_test", DEFAULTS["filter_test"]).copy()


def get_generator_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section generator (paramètres par défaut générateur)."""
    return config.get("generator", DEFAULTS["generator"]).copy()


def get_logging_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section logging (output_dir, level, etc.)."""
    return config.get("logging", DEFAULTS["logging"]).copy()


def get_bode_viewer_config(config: dict[str, Any]) -> dict[str, Any]:
    """Retourne la section bode_viewer (options de la fenêtre graphique Bode)."""
    return config.get("bode_viewer", DEFAULTS["bode_viewer"]).copy()
