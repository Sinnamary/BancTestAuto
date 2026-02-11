"""
Stub SerialConnection pour la maquette : pas d'ouverture de port.
"""

class SerialConnection:
    def __init__(self, port=None, baudrate=9600, **kwargs):
        self._port = port
        self._open = False

    def open(self):
        self._open = True

    def close(self):
        self._open = False

    def is_open(self):
        return self._open

    def write(self, data: bytes) -> int:
        return 0

    def read(self, size=1) -> bytes:
        return b""

    def readline(self) -> bytes:
        return b""

    def reset_input_buffer(self):
        pass

    def reset_output_buffer(self):
        pass
