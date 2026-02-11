"""
Tests de core.connection_controller_impl.CallbackConnectionController avec callbacks mockés.
"""
from unittest.mock import MagicMock

import pytest

from core.equipment import EquipmentKind
from core.equipment_state import BenchConnectionState, EquipmentState
from core.connection_controller_impl import CallbackConnectionController


class TestCallbackConnectionController:
    """Contrôleur par délégation : apply_config, connect_all, disconnect_all, get_state, connect, disconnect."""

    def test_connect_all_calls_callback(self):
        on_connect = MagicMock()
        on_disconnect = MagicMock()
        on_get_state = MagicMock(return_value=BenchConnectionState())
        ctrl = CallbackConnectionController(
            on_connect_all=on_connect,
            on_disconnect_all=on_disconnect,
            on_get_state=on_get_state,
        )
        ctrl.connect_all()
        on_connect.assert_called_once()
        on_disconnect.assert_not_called()

    def test_disconnect_all_calls_callback(self):
        on_connect = MagicMock()
        on_disconnect = MagicMock()
        on_get_state = MagicMock(return_value=BenchConnectionState())
        ctrl = CallbackConnectionController(
            on_connect_all=on_connect,
            on_disconnect_all=on_disconnect,
            on_get_state=on_get_state,
        )
        ctrl.disconnect_all()
        on_disconnect.assert_called_once()
        on_connect.assert_not_called()

    def test_get_state_returns_callback_result(self):
        state = BenchConnectionState()
        state.set_state(EquipmentKind.MULTIMETER, connected=True, port_or_device="COM3")
        on_get_state = MagicMock(return_value=state)
        ctrl = CallbackConnectionController(
            on_connect_all=MagicMock(),
            on_disconnect_all=MagicMock(),
            on_get_state=on_get_state,
        )
        out = ctrl.get_state()
        on_get_state.assert_called_once()
        assert out is state
        assert out.is_connected(EquipmentKind.MULTIMETER) is True

    def test_apply_config_stores_and_calls_optional_callback(self):
        on_apply = MagicMock()
        ctrl = CallbackConnectionController(
            on_connect_all=MagicMock(),
            on_disconnect_all=MagicMock(),
            on_get_state=MagicMock(return_value=BenchConnectionState()),
            on_apply_config=on_apply,
        )
        config = {"serial_multimeter": {"port": "COM5"}}
        ctrl.apply_config(config)
        assert ctrl._config == config
        on_apply.assert_called_once_with(config)

    def test_apply_config_without_callback_uses_no_op(self):
        ctrl = CallbackConnectionController(
            on_connect_all=MagicMock(),
            on_disconnect_all=MagicMock(),
            on_get_state=MagicMock(return_value=BenchConnectionState()),
        )
        config = {"serial_generator": {"port": "COM4"}}
        ctrl.apply_config(config)
        assert ctrl._config == config

    def test_connect_kind_delegates_to_connect_all(self):
        on_connect = MagicMock()
        ctrl = CallbackConnectionController(
            on_connect_all=on_connect,
            on_disconnect_all=MagicMock(),
            on_get_state=MagicMock(return_value=BenchConnectionState()),
        )
        ctrl.connect(EquipmentKind.GENERATOR)
        on_connect.assert_called_once()

    def test_disconnect_kind_delegates_to_disconnect_all(self):
        on_disconnect = MagicMock()
        ctrl = CallbackConnectionController(
            on_connect_all=MagicMock(),
            on_disconnect_all=on_disconnect,
            on_get_state=MagicMock(return_value=BenchConnectionState()),
        )
        ctrl.disconnect(EquipmentKind.OSCILLOSCOPE)
        on_disconnect.assert_called_once()
