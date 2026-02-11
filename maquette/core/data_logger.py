"""
Stub DataLogger pour la maquette.
"""

class DataLogger:
    def __init__(self, output_dir, **kwargs):
        pass

    def start(self, mode_scpi: str) -> None:
        pass

    def stop(self) -> None:
        pass

    def log_measurement(self, value: float, unit: str) -> None:
        pass

    def is_logging(self) -> bool:
        return False
