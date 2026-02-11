"""
Stub SerialExchangeLogger pour la maquette.
"""

class SerialExchangeLogger:
    def __init__(self, enabled: bool = False):
        pass

    def log_tx(self, port: str, data: bytes) -> None:
        pass

    def log_rx(self, port: str, data: bytes) -> None:
        pass
