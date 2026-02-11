"""Tests du chargement CSV (BodeCsvColumnMap, BodeCsvFileLoader)."""
import pytest

from ui.bode_csv_viewer.csv_loader import BodeCsvColumnMap, BodeCsvFileLoader


class TestBodeCsvColumnMap:
    def test_standard_header(self):
        header = ["f_Hz", "Us_V", "Us_Ue", "Gain_dB"]
        m = BodeCsvColumnMap(header)
        assert m.get("f_hz") == 0
        assert m.get("us_v") == 1
        assert m.get("gain_linear") == 2
        assert m.get("gain_db") == 3

    def test_case_insensitive(self):
        m = BodeCsvColumnMap(["F_HZ", "US_V", "Us_Ue", "GAIN_DB"])
        assert m.get("f_hz") == 0
        assert m.get("gain_db") == 3

    def test_defaults_when_missing(self):
        m = BodeCsvColumnMap(["A", "B", "C", "D"])
        assert m.get("f_hz") == 0
        assert m.get("gain_db") == 3
        assert m.get("us_v") == 1
        assert m.get("gain_linear") == 2


class TestBodeCsvFileLoader:
    def test_empty_file(self, bode_csv_dir):
        p = bode_csv_dir / "empty.csv"
        p.write_text("", encoding="utf-8")
        loader = BodeCsvFileLoader()
        ds = loader.load(str(p))
        assert ds.is_empty()

    def test_header_only(self, bode_csv_dir):
        p = bode_csv_dir / "head.csv"
        p.write_text("f_Hz;Us_V;Us_Ue;Gain_dB\n", encoding="utf-8")
        loader = BodeCsvFileLoader()
        ds = loader.load(str(p))
        assert ds.count == 0

    def test_one_row(self, bode_csv_dir):
        p = bode_csv_dir / "one.csv"
        p.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n"
            "100.0;0.707;0.707;-3.0\n",
            encoding="utf-8",
        )
        loader = BodeCsvFileLoader()
        ds = loader.load(str(p))
        assert ds.count == 1
        pt = ds.points[0]
        assert pt.f_hz == 100.0
        assert pt.gain_db == pytest.approx(-3.0)
        assert pt.gain_linear == pytest.approx(0.707, rel=1e-2)

    def test_several_rows(self, bode_csv_dir):
        p = bode_csv_dir / "multi.csv"
        lines = ["f_Hz;Us_V;Us_Ue;Gain_dB\n"]
        for i, f in enumerate([10.0, 100.0, 1000.0]):
            g_db = 0.0 - i * 3.0
            g_lin = 10 ** (g_db / 20.0)
            lines.append(f"{f};{g_lin};{g_lin};{g_db}\n")
        p.write_text("".join(lines), encoding="utf-8")
        loader = BodeCsvFileLoader()
        ds = loader.load(str(p))
        assert ds.count == 3
        assert ds.freqs_hz() == [10.0, 100.0, 1000.0]

    def test_comma_decimal(self, bode_csv_dir):
        p = bode_csv_dir / "comma.csv"
        p.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n"
            "50,5;1,0;1,0;0\n",
            encoding="utf-8",
        )
        loader = BodeCsvFileLoader()
        ds = loader.load(str(p))
        assert ds.count == 1
        assert ds.points[0].f_hz == 50.5

    def test_short_row_skipped(self, bode_csv_dir):
        p = bode_csv_dir / "short.csv"
        p.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n"
            "100;0.7;0.7;-3\n"
            "200\n"
            "300;0.5;0.5;-6\n",
            encoding="utf-8",
        )
        loader = BodeCsvFileLoader()
        ds = loader.load(str(p))
        assert ds.count == 2

    def test_db_to_linear(self):
        assert BodeCsvFileLoader._db_to_linear(-200) == 0.0
        assert BodeCsvFileLoader._db_to_linear(0) == pytest.approx(1.0)
        assert BodeCsvFileLoader._db_to_linear(-20) == pytest.approx(0.1, rel=1e-2)
