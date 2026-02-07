"""
Fixtures partagées pour les tests.
Fournit des mocks pour la série, des chemins temporaires, etc.
"""
import sys
from pathlib import Path

import pytest

# Racine du projet pour les imports
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


@pytest.fixture
def tmp_config_path(tmp_path):
    """Répertoire temporaire contenant un config.json (optionnel)."""
    return tmp_path / "config.json"


@pytest.fixture
def mock_serial():
    """Mock de serial.Serial pour tester SerialConnection sans port réel."""
    class MockSerial:
        def __init__(self, **kwargs):
            self._open = True
            self._written = []

        @property
        def is_open(self):
            return self._open

        def close(self):
            self._open = False

        def write(self, data):
            self._written.append(data)
            return len(data)

        def readline(self):
            return b"1.234E+00\n"

        def read_until(self, terminator=b"\n"):
            return b"1.234E+00\n"
    return MockSerial


@pytest.fixture
def mock_connection(mock_serial):
    """Instance de SerialConnection avec un mock à la place de serial.Serial."""
    from unittest.mock import patch, MagicMock
    from core.serial_connection import SerialConnection

    with patch("serial.Serial", mock_serial):
        conn = SerialConnection(port="COM99", baudrate=9600)
        conn.open()
        yield conn
        conn.close()
