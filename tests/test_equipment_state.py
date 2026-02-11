"""
Tests de core.equipment_state : EquipmentState, BenchConnectionState, display_text, get_state, set_state, is_connected, is_any_connected, all_kinds.
"""
import pytest

from core.equipment import EquipmentKind
from core.equipment_state import BenchConnectionState, EquipmentState


class TestEquipmentState:
    """État d'un équipement : connecté, port, modèle, display_text."""

    def test_default_not_connected(self):
        s = EquipmentState(kind=EquipmentKind.MULTIMETER)
        assert s.connected is False
        assert s.port_or_device is None
        assert s.model_or_label is None
        assert s.detected is False

    def test_display_text_not_connected(self):
        s = EquipmentState(kind=EquipmentKind.GENERATOR)
        assert "Non connecté" in s.display_text()
        assert "Générateur" in s.display_text()

    def test_display_text_connected_with_model_and_port(self):
        s = EquipmentState(
            kind=EquipmentKind.MULTIMETER,
            connected=True,
            port_or_device="COM3",
            model_or_label="XDM",
        )
        text = s.display_text()
        assert "Multimètre" in text
        assert "XDM" in text
        assert "COM3" in text

    def test_display_text_connected_model_only(self):
        s = EquipmentState(
            kind=EquipmentKind.OSCILLOSCOPE,
            connected=True,
            model_or_label="DOS1102",
        )
        assert "DOS1102" in s.display_text()
        assert "Oscilloscope" in s.display_text()

    def test_display_text_connected_port_only(self):
        s = EquipmentState(
            kind=EquipmentKind.POWER_SUPPLY,
            connected=True,
            port_or_device="COM6",
        )
        assert "COM6" in s.display_text()
        assert "Alimentation" in s.display_text()


class TestBenchConnectionState:
    """État du banc : get_state, set_state, is_connected, is_any_connected, all_kinds."""

    def test_post_init_creates_states_for_all_kinds(self):
        bench = BenchConnectionState()
        kinds = bench.all_kinds()
        assert EquipmentKind.MULTIMETER in kinds
        assert EquipmentKind.GENERATOR in kinds
        assert EquipmentKind.POWER_SUPPLY in kinds
        assert EquipmentKind.OSCILLOSCOPE in kinds
        for k in kinds:
            assert bench.get_state(k).kind == k
            assert bench.get_state(k).connected is False

    def test_set_state_and_get_state(self):
        bench = BenchConnectionState()
        bench.set_state(
            EquipmentKind.MULTIMETER,
            connected=True,
            port_or_device="COM3",
            model_or_label="XDM",
        )
        s = bench.get_state(EquipmentKind.MULTIMETER)
        assert s.connected is True
        assert s.port_or_device == "COM3"
        assert s.model_or_label == "XDM"

    def test_set_state_detected(self):
        bench = BenchConnectionState()
        bench.set_state(EquipmentKind.GENERATOR, connected=False, detected=True)
        s = bench.get_state(EquipmentKind.GENERATOR)
        assert s.detected is True
        assert s.connected is False

    def test_is_connected(self):
        bench = BenchConnectionState()
        assert bench.is_connected(EquipmentKind.MULTIMETER) is False
        bench.set_state(EquipmentKind.MULTIMETER, connected=True)
        assert bench.is_connected(EquipmentKind.MULTIMETER) is True

    def test_is_any_connected_none(self):
        bench = BenchConnectionState()
        assert bench.is_any_connected() is False

    def test_is_any_connected_one(self):
        bench = BenchConnectionState()
        bench.set_state(EquipmentKind.POWER_SUPPLY, connected=True)
        assert bench.is_any_connected() is True

    def test_get_state_creates_missing_kind(self):
        bench = BenchConnectionState()
        del bench._states[EquipmentKind.OSCILLOSCOPE]
        s = bench.get_state(EquipmentKind.OSCILLOSCOPE)
        assert s.kind == EquipmentKind.OSCILLOSCOPE
        assert s.connected is False

    def test_all_kinds_order(self):
        bench = BenchConnectionState()
        kinds = bench.all_kinds()
        assert kinds == [
            EquipmentKind.MULTIMETER,
            EquipmentKind.GENERATOR,
            EquipmentKind.POWER_SUPPLY,
            EquipmentKind.OSCILLOSCOPE,
        ]
