"""
Tests du module core.dos1102_measurements : formatage mesures, phase (sans UI).
"""
import pytest

from core.dos1102_measurements import (
    format_meas_general_response,
    format_measurements_text,
    phase_deg_from_delay,
    get_measure_types_per_channel,
    get_measure_types_inter_channel,
)


class TestFormatMeasGeneralResponse:
    def test_empty_returns_dash(self):
        assert format_meas_general_response("") == "—"
        assert format_meas_general_response("   ") == "—"
        assert format_meas_general_response(None) == "—"

    def test_plain_text_passthrough(self):
        assert format_meas_general_response("CH1: 1.5V") == "CH1: 1.5V"

    def test_json_dict_formatted(self):
        text = '{"CH1":{"PERiod":"0.001"}}'
        out = format_meas_general_response(text)
        assert "CH1" in out
        assert "PERiod" in out or "0.001" in out

    def test_bytes_decoded(self):
        out = format_meas_general_response(b"1.0,2.0")
        assert "1.0" in out and "2.0" in out


class TestFormatMeasurementsText:
    def test_one_per_line(self):
        m = {"Période": "0.001", "Fréquence": "1000"}
        out = format_measurements_text(m)
        assert "Période: 0.001" in out
        assert "Fréquence: 1000" in out

    def test_add_bode_hint(self):
        out = format_measurements_text({"A": "1"}, add_bode_hint=True)
        assert "Bode" in out or "phase" in out or "délai" in out


class TestPhaseDegFromDelay:
    def test_formula(self):
        # 90° = délai quart de période
        assert phase_deg_from_delay(0.00025, 0.001) == pytest.approx(90.0)
        assert phase_deg_from_delay(0.0005, 0.001) == pytest.approx(180.0)
        assert phase_deg_from_delay(0.0, 0.001) == pytest.approx(0.0)

    def test_period_zero_returns_none(self):
        assert phase_deg_from_delay(0.001, 0) is None
        assert phase_deg_from_delay(0.001, -0.001) is None

    def test_none_period_returns_none(self):
        assert phase_deg_from_delay(0.001, None) is None


class TestGetMeasureTypes:
    def test_per_channel_list(self):
        lst = get_measure_types_per_channel()
        assert isinstance(lst, list)
        assert len(lst) > 0
        label, scpi = lst[0]
        assert isinstance(label, str) and isinstance(scpi, str)

    def test_inter_channel_list(self):
        lst = get_measure_types_inter_channel()
        assert isinstance(lst, list)
