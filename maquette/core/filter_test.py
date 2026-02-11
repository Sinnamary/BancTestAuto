"""
Stub FilterTest pour la maquette.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class BodePoint:
    f_hz: float
    us_v: float
    gain_linear: float
    gain_db: float


@dataclass
class FilterTestConfig:
    generator_channel: int
    f_min_hz: float
    f_max_hz: float
    points_per_decade: int
    scale: str
    settling_ms: int
    ue_rms: float


class FilterTest:
    def __init__(self, generator, measurement, config: FilterTestConfig):
        self._config = config

    def set_config(self, config: FilterTestConfig) -> None:
        pass

    def abort(self) -> None:
        pass

    def run(self, progress_callback=None) -> list:
        return []
