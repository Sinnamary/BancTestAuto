"""
Tests du module core.dos1102_waveform : décodage forme d'onde DOS1102 (sans UI).
"""
import pytest

from core.dos1102_waveform import (
    decode_screen_channel,
    time_base_from_meta,
    decode_screen_waveform,
    parse_ascii_waveform,
    waveform_display_summary,
)


class TestDecodeScreenChannel:
    def test_minimal_binary(self):
        # 4 octets à ignorer + paires int16 LE ; meta avec OFFSET et SCALE
        meta = {
            "CHANNEL": [
                {"SCALE": "1V", "OFFSET": "0", "PROBE": "X1"},
                {"SCALE": "1V", "OFFSET": "0", "PROBE": "X1"},
            ]
        }
        # 4 bytes skip + 2*2 = 4 bytes (2 points) : valeurs 0, 410 (1 div)
        raw = bytes([0, 0, 0, 0]) + (0).to_bytes(2, "little", signed=True) + (410).to_bytes(2, "little", signed=True)
        out = decode_screen_channel(raw, meta, 1)
        assert isinstance(out, list)
        assert len(out) == 2
        assert out[0] == pytest.approx(0.0, abs=1e-6)
        # scale * (410 - 0*8.25) / 410 = 1 * 410/410 = 1.0
        assert out[1] == pytest.approx(1.0, abs=1e-5)

    def test_scale_mv(self):
        meta = {
            "CHANNEL": [
                {"SCALE": "100mV", "OFFSET": "0", "PROBE": "X1"},
                {"SCALE": "1V", "OFFSET": "0", "PROBE": "X1"},
            ]
        }
        raw = bytes([0] * 4) + (0).to_bytes(2, "little", signed=True)
        out = decode_screen_channel(raw, meta, 1)
        assert len(out) == 1
        assert out[0] == pytest.approx(0.0, abs=1e-9)


class TestTimeBaseFromMeta:
    def test_basic(self):
        meta = {
            "SAMPLE": {"DATALEN": "1400", "SAMPLERATE": "1kS/s"},
            "TIMEBASE": {"HOFFSET": "0"},
        }
        t = time_base_from_meta(meta)
        assert isinstance(t, list)
        assert len(t) == 1400
        # t[k] = (k - nbr_points/2) * sample_time - time_offset ; sample_time = 5.0/1000
        # t[0] = (0 - 700) * 0.005 = -3.5
        assert t[0] == pytest.approx(-3.5, abs=1e-6)

    def test_ms_s_units(self):
        meta = {
            "SAMPLE": {"DATALEN": "100", "SAMPLERATE": "1MS/s"},
            "TIMEBASE": {"HOFFSET": "0"},
        }
        t = time_base_from_meta(meta)
        assert len(t) == 100


class TestDecodeScreenWaveform:
    def test_returns_three_arrays(self):
        meta = {
            "CHANNEL": [
                {"SCALE": "1V", "OFFSET": "0", "PROBE": "X1"},
                {"SCALE": "1V", "OFFSET": "0", "PROBE": "X1"},
            ],
            "SAMPLE": {"DATALEN": "2", "SAMPLERATE": "1kS/s"},
            "TIMEBASE": {"HOFFSET": "0"},
        }
        raw1 = bytes([0] * 4) + (0).to_bytes(2, "little", signed=True) + (100).to_bytes(2, "little", signed=True)
        raw2 = bytes([0] * 4) + (50).to_bytes(2, "little", signed=True) + (200).to_bytes(2, "little", signed=True)
        time_arr, ch1_arr, ch2_arr = decode_screen_waveform(meta, raw1, raw2)
        assert len(time_arr) == 2
        assert len(ch1_arr) == 2
        assert len(ch2_arr) == 2


class TestParseAsciiWaveform:
    def test_string_numbers(self):
        out = parse_ascii_waveform("1.0, 2.0, 3.0")
        assert out == [1.0, 2.0, 3.0]

    def test_spaces_and_commas(self):
        out = parse_ascii_waveform("  1  2  3  ")
        assert out == [1.0, 2.0, 3.0]

    def test_bytes_utf8(self):
        out = parse_ascii_waveform(b"0.5, -0.5")
        assert out == [0.5, -0.5]

    def test_empty_returns_none(self):
        assert parse_ascii_waveform("") is None
        assert parse_ascii_waveform("   ") is None

    def test_invalid_returns_partial(self):
        out = parse_ascii_waveform("1.0, xxx, 2.0")
        assert out == [1.0, 2.0]


class TestWaveformDisplaySummary:
    def test_string_returns_as_is(self):
        assert waveform_display_summary("1,2,3") == "1,2,3"

    def test_bytes_returns_binary_summary(self):
        out = waveform_display_summary(bytes([0] * 100))
        assert "binaire" in out and "100" in out

    def test_empty_string(self):
        assert waveform_display_summary("") == "—"
