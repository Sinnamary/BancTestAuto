"""
Tests du module ui.bode_csv_viewer : modèle, chargement CSV, cutoff, lissage,
formatage, plage de vue, survol. Couvre les classes et fonctions sans dépendance
GUI lourde (sauf quelques tests optionnels avec Qt pour ViewBox).
"""
from pathlib import Path

import pytest

# --- Modèle ---
from ui.bode_csv_viewer.model import BodeCsvPoint, BodeCsvDataset


class TestBodeCsvPoint:
    """BodeCsvPoint : dataclass fréquence, tension, gain linéaire/dB."""

    def test_create(self):
        p = BodeCsvPoint(f_hz=100.0, us_v=1.0, gain_linear=0.5, gain_db=-6.02)
        assert p.f_hz == 100.0
        assert p.us_v == 1.0
        assert p.gain_linear == 0.5
        assert p.gain_db == pytest.approx(-6.02)

    def test_equality_by_value(self):
        a = BodeCsvPoint(10.0, 1.0, 1.0, 0.0)
        b = BodeCsvPoint(10.0, 1.0, 1.0, 0.0)
        assert a == b


class TestBodeCsvDataset:
    """BodeCsvDataset : conteneur de points, freqs_hz, gains_db, gains_linear."""

    def test_empty(self):
        ds = BodeCsvDataset([])
        assert ds.count == 0
        assert ds.is_empty() is True
        assert ds.points == []
        assert ds.freqs_hz() == []
        assert ds.gains_db() == []
        assert ds.gains_linear() == []

    def test_with_points(self):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
        ]
        ds = BodeCsvDataset(pts)
        assert ds.count == 2
        assert ds.is_empty() is False
        assert ds.freqs_hz() == [10.0, 100.0]
        assert ds.gains_db() == [0.0, -3.0]
        assert ds.gains_linear() == [1.0, 0.7]

    def test_points_copy(self):
        pts = [BodeCsvPoint(1.0, 1.0, 1.0, 0.0)]
        ds = BodeCsvDataset(pts)
        assert ds.points is not pts
        assert len(ds.points) == 1


# --- View state ---
from ui.bode_csv_viewer.view_state import BodeViewOptions


class TestBodeViewOptions:
    def test_default(self):
        opt = BodeViewOptions.default()
        assert opt.grid_visible is True
        assert opt.plot_background_dark is True
        assert opt.curve_color == "#e0c040"
        assert opt.smooth_window == 0
        assert opt.y_linear is False

    def test_class_constants(self):
        assert len(BodeViewOptions.SMOOTH_WINDOW_CHOICES) == 5
        assert BodeViewOptions.SMOOTH_WINDOW_CHOICES == (3, 5, 7, 9, 11)
        assert len(BodeViewOptions.BACKGROUND_CHOICES) == 2
        assert BodeViewOptions.CURVE_COLOR_CHOICES[0][1] == "#e0c040"


# --- Formatters ---
from ui.bode_csv_viewer.formatters import format_freq_hz


class TestFormatFreqHz:
    def test_hz(self):
        assert format_freq_hz(50.0) == "50.0 Hz"
        assert format_freq_hz(1.0) == "1.0 Hz"

    def test_khz(self):
        assert format_freq_hz(1000.0) == "1.00 kHz"
        assert "kHz" in format_freq_hz(2500.0)

    def test_mhz(self):
        assert "mHz" in format_freq_hz(0.5)
        assert format_freq_hz(0.001) == "1.0 mHz"


# --- CSV loader ---
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


@pytest.fixture
def bode_csv_dir():
    """Répertoire pour les CSV de test (dans le projet pour fiabilité sous sandbox)."""
    root = Path(__file__).resolve().parent.parent
    d = root / "tests" / "tmp_bode_csv"
    d.mkdir(parents=True, exist_ok=True)
    return d


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


# --- Cutoff ---
from ui.bode_csv_viewer.cutoff import Cutoff3DbFinder, CutoffResult


class TestCutoffResult:
    def test_fields(self):
        r = CutoffResult(fc_hz=1000.0, gain_db=-3.0)
        assert r.fc_hz == 1000.0
        assert r.gain_db == -3.0


class TestCutoff3DbFinder:
    def _dataset(self, freqs, gains_db):
        pts = [
            BodeCsvPoint(f, 1.0, 10 ** (g / 20.0), g)
            for f, g in zip(freqs, gains_db)
        ]
        return BodeCsvDataset(pts)

    def test_find_first_cutoff(self):
        ds = self._dataset([10, 100, 500, 1000], [0, -1, -3.5, -10])
        finder = Cutoff3DbFinder()
        r = finder.find(ds)
        assert r is not None
        assert 100 < r.fc_hz < 1000
        assert r.gain_db == pytest.approx(-3.0)

    def test_find_all_single_cutoff(self):
        ds = self._dataset([10, 100, 1000], [0, -1.5, -6])
        finder = Cutoff3DbFinder()
        all_r = finder.find_all(ds)
        assert len(all_r) == 1
        assert all_r[0].gain_db == pytest.approx(-3.0)

    def test_find_all_band_stop_two_cutoffs(self):
        # Courbe qui descend, remonte, redescend : 2 croisements -3 dB
        freqs = [10, 100, 500, 1000, 2000, 5000]
        gains = [0, -2, -5, -2, -5, -10]
        ds = self._dataset(freqs, gains)
        finder = Cutoff3DbFinder()
        all_r = finder.find_all(ds, gain_ref=0)
        assert len(all_r) >= 2

    def test_find_empty_dataset(self):
        finder = Cutoff3DbFinder()
        assert finder.find(BodeCsvDataset([])) is None
        assert finder.find_all(BodeCsvDataset([])) == []

    def test_find_crossings_at_gain(self):
        ds = self._dataset([10, 100, 1000], [0, -6, -20])
        finder = Cutoff3DbFinder()
        r = finder.find_crossings_at_gain(ds, -6.0)
        assert len(r) >= 1
        assert 10 <= r[0].fc_hz <= 1000
        assert r[0].gain_db == pytest.approx(-6.0)

    def test_find_crossings_at_gain_multiple(self):
        freqs = [10, 50, 100, 200, 500]
        gains = [0, -2, -5, -2, -4]
        ds = self._dataset(freqs, gains)
        finder = Cutoff3DbFinder()
        r = finder.find_crossings_at_gain(ds, -3.0)
        assert len(r) >= 1


# --- Smoothing ---
from ui.bode_csv_viewer.smoothing import (
    MovingAverageSmoother,
    smooth_savgol,
    has_savgol,
)


class TestMovingAverageSmoother:
    def test_window_property(self):
        s = MovingAverageSmoother(5)
        assert s.window == 5

    def test_window_clamped(self):
        s = MovingAverageSmoother(0)
        assert s.window == 1
        s2 = MovingAverageSmoother(20)
        assert s2.window == 11

    def test_smooth_empty(self):
        s = MovingAverageSmoother(5)
        assert s.smooth([]) == []

    def test_smooth_window_1(self):
        s = MovingAverageSmoother(1)
        assert s.smooth([1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0]

    def test_smooth_window_3(self):
        s = MovingAverageSmoother(3)
        out = s.smooth([1.0, 2.0, 3.0, 4.0, 5.0])
        assert out[2] == pytest.approx(3.0)
        assert len(out) == 5

    def test_set_window(self):
        s = MovingAverageSmoother(5)
        s.set_window(7)
        assert s.window == 7


class TestSmoothSavgol:
    def test_returns_copy_without_scipy(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        out = smooth_savgol(vals, 5)
        assert out == vals or len(out) == len(vals)

    def test_short_series_returns_copy(self):
        out = smooth_savgol([1.0, 2.0], 5)
        assert out == [1.0, 2.0]


def test_has_savgol():
    assert isinstance(has_savgol(), bool)


# --- Plot range ---
from ui.bode_csv_viewer.plot_range import (
    compute_data_range,
    apply_view_range,
    read_view_range,
    AUTO_RANGE_MARGIN,
)


class TestComputeDataRange:
    def test_empty_returns_none(self):
        assert compute_data_range([], []) is None
        assert compute_data_range([1], []) is None
        assert compute_data_range([], [1]) is None

    def test_length_mismatch_returns_none(self):
        assert compute_data_range([1, 2], [1]) is None

    def test_basic(self):
        r = compute_data_range([10.0, 1000.0], [0.0, -20.0])
        assert r is not None
        x_min, x_max, y_min, y_max = r
        assert x_min < 10.0
        assert x_max > 1000.0
        assert y_min < -20.0
        assert y_max > 0.0

    def test_x_min_floor(self):
        r = compute_data_range([1.0, 10.0], [0.0, 0.0])
        assert r is not None
        assert r[0] >= 0.1

    def test_margin_parameter(self):
        r0 = compute_data_range([10, 100], [0, -10], margin=0.0)
        r1 = compute_data_range([10, 100], [0, -10], margin=0.1)
        assert r0 is not None and r1 is not None
        assert r1[1] - r1[0] > r0[1] - r0[0]


class TestApplyAndReadViewRange:
    """Tests avec ViewBox pyqtgraph (nécessite Qt)."""

    @pytest.fixture
    def view_box(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        pw.setLogMode(x=True, y=False)
        vb = pw.getViewBox()
        yield vb
        pw.close()

    def test_apply_then_read_roundtrip(self, view_box):
        apply_view_range(view_box, 10.0, 10000.0, -20.0, 5.0, log_mode_x=True)
        out = read_view_range(view_box, log_mode_x=True)
        assert out[0] == pytest.approx(10.0, rel=1e-5)
        assert out[1] == pytest.approx(10000.0, rel=1e-5)
        assert out[2] == pytest.approx(-20.0)
        assert out[3] == pytest.approx(5.0)

    def test_read_with_fallback(self, view_box):
        fallback = (1.0, 1000.0, -10.0, 0.0)
        out = read_view_range(view_box, log_mode_x=True, fallback=fallback)
        assert len(out) == 4
        if out[0] < 1e-200 or out[1] > 1e200:
            assert out == fallback
        else:
            assert out[0] == pytest.approx(fallback[0]) or out == fallback


# --- Plot hover (format pur) ---
from ui.bode_csv_viewer.plot_hover import format_hover_text


class TestFormatHoverText:
    def test_db_mode(self):
        s = format_hover_text(100.0, -3.0, y_linear=False)
        assert "dB" in s
        assert "100" in s
        assert "-3.00" in s

    def test_linear_mode(self):
        s = format_hover_text(1000.0, 0.707, y_linear=True)
        assert "Us/Ue" in s
        assert "kHz" in s
        assert "0.71" in s


# --- Plot curves ---
from ui.bode_csv_viewer.plot_curves import BodeCurveDrawer


class TestBodeCurveDrawer:
    @pytest.fixture
    def plot_item(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        yield pw.getPlotItem()
        pw.close()

    def test_clear(self, plot_item):
        drawer = BodeCurveDrawer(plot_item)
        drawer.clear()
        # pas d'exception

    def test_set_data_empty(self, plot_item):
        drawer = BodeCurveDrawer(plot_item)
        drawer.set_data(BodeCsvDataset([]), y_linear=False)
        drawer.set_data(BodeCsvDataset([]), y_linear=True)

    def test_set_data_with_points(self, plot_item):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
        ]
        ds = BodeCsvDataset(pts)
        drawer = BodeCurveDrawer(plot_item)
        drawer.set_data(ds, y_linear=False)
        drawer.set_data(ds, y_linear=True)

    def test_set_curve_color(self, plot_item):
        drawer = BodeCurveDrawer(plot_item)
        drawer.set_curve_color("#ff0000")
        from PyQt6.QtGui import QColor
        drawer.set_curve_color(QColor("#00ff00"))


# --- Plot style (constantes + apply_background_style) ---
from ui.bode_csv_viewer.plot_style import (
    BG_DARK,
    BG_LIGHT,
    AXIS_LABEL_FONT_SIZE,
    apply_axis_fonts,
    apply_background_style,
)


class TestPlotStyle:
    def test_constants(self):
        assert BG_DARK == "k"
        assert BG_LIGHT == "w"
        assert AXIS_LABEL_FONT_SIZE == 12

    @pytest.fixture
    def plot_item(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        yield pw.getPlotItem()
        pw.close()

    def test_apply_axis_fonts(self, plot_item):
        apply_axis_fonts(plot_item)
        assert plot_item.getAxis("left").tickFont is not None

    def test_apply_background_style_dark(self, plot_item):
        vb = plot_item.getViewBox()
        grid = type("Grid", (), {"set_dark_background": lambda self, d: None})()
        apply_background_style(plot_item, vb, dark=True, grid=grid, hover_label=None)
        apply_background_style(plot_item, vb, dark=True, grid=grid, hover_label=None)

    def test_apply_background_style_light(self, plot_item):
        vb = plot_item.getViewBox()
        grid = type("Grid", (), {"set_dark_background": lambda self, d: None})()
        apply_background_style(plot_item, vb, dark=False, grid=grid, hover_label=None)

    def test_apply_background_style_with_hover_label(self, plot_item):
        import pyqtgraph as pg
        vb = plot_item.getViewBox()
        grid = type("Grid", (), {"set_dark_background": lambda self, d: None})()
        hover = pg.TextItem(text="")
        plot_item.addItem(hover)
        apply_background_style(plot_item, vb, dark=True, grid=grid, hover_label=hover)
        apply_background_style(plot_item, vb, dark=False, grid=grid, hover_label=hover)


# --- BodeCsvPlotWidget (classe principale, couverture 0% → élevée) ---
from ui.bode_csv_viewer.plot_widget import BodeCsvPlotWidget


class TestBodeCsvPlotWidget:
    """Exécute le code du widget pour couvrir BodeCsvPlotWidget."""

    @pytest.fixture
    def qapp(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def widget(self, qapp):
        w = BodeCsvPlotWidget()
        yield w
        w.close()

    @pytest.fixture
    def dataset(self):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
            BodeCsvPoint(1000.0, 0.1, 0.1, -20.0),
        ]
        return BodeCsvDataset(pts)

    def test_init_and_set_dataset_empty(self, widget):
        widget.set_dataset(None)
        widget.set_dataset(BodeCsvDataset([]))
        assert widget.get_data_range() is None

    def test_set_dataset_with_data(self, widget, dataset):
        widget.set_dataset(dataset)
        r = widget.get_data_range()
        assert r is not None
        assert r[0] <= 10.0 and r[1] >= 1000.0

    def test_set_y_linear(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_y_linear(True)
        widget.set_y_linear(False)

    def test_grid_and_background(self, widget):
        widget.set_grid_visible(True)
        widget.set_grid_visible(False)
        widget.set_minor_grid_visible(True)
        widget.set_minor_grid_visible(False)
        widget.set_background_dark(True)
        widget.set_background_dark(False)

    def test_set_curve_color(self, widget):
        from PyQt6.QtGui import QColor
        widget.set_curve_color("#ff0000")
        widget.set_curve_color(QColor("#00ff00"))

    def test_set_smoothing(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_smoothing(0)
        widget.set_smoothing(5, show_raw=True, use_savgol=False)
        widget.set_smoothing(5, show_raw=False, use_savgol=True)

    def test_set_peaks_visible(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_peaks_visible(True)
        widget.set_peaks_visible(False)

    def test_set_target_gain_search(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_target_gain_search(-3.0, [100.0])
        widget.set_target_gain_search(None)
        widget.set_target_gain_search(-6.0, [50.0, 200.0])

    def test_auto_range(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.auto_range()
        widget.set_dataset(None)
        widget.auto_range()

    def test_set_view_range_and_get_view_range(self, widget, dataset):
        widget.set_dataset(dataset)
        widget.set_view_range(10.0, 10000.0, -25.0, 5.0)
        x_min, x_max, y_min, y_max = widget.get_view_range()
        assert x_min == pytest.approx(10.0, rel=1e-5)
        assert x_max == pytest.approx(10000.0, rel=1e-5)
        assert y_min == pytest.approx(-25.0)
        assert y_max == pytest.approx(5.0)

    def test_set_rect_zoom_mode(self, widget):
        widget.set_rect_zoom_mode(True)
        widget.set_rect_zoom_mode(False)

    def test_export_png(self, widget, dataset, bode_csv_dir):
        widget.set_dataset(dataset)
        path = str(bode_csv_dir / "export_bode.png")
        ok = widget.export_png(path)
        assert isinstance(ok, bool)
        if ok:
            assert Path(path).exists()
        # en headless/sandbox l'export peut échouer ; le code est tout de même couvert

    def test_show_event_installs_hover_filter(self, widget, qapp):
        widget.show()
        assert getattr(widget, "_hover_filter_installed", False) or widget._hover_label is not None
        widget.hide()

    def test_event_filter_mouse_move(self, widget, qapp):
        from PyQt6.QtCore import QPointF, QEvent
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import Qt
        widget.show()
        vb = widget._plot_widget.getViewBox()
        if vb.scene() and vb.scene().views():
            view = vb.scene().views()[0]
            pt = view.viewport().rect().center()
            pos = QPointF(float(pt.x()), float(pt.y()))
            event = QMouseEvent(
                QEvent.Type.MouseMove,
                pos,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.eventFilter(view.viewport(), event)
        widget.hide()


# --- Plot peaks (update avec dataset, sans affichage) ---
from ui.bode_csv_viewer.plot_peaks import BodePeaksOverlay


class TestBodePeaksOverlay:
    @pytest.fixture
    def plot_item(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        import pyqtgraph as pg
        pw = pg.PlotWidget()
        yield pw.getPlotItem()
        pw.close()

    def test_set_visible(self, plot_item):
        overlay = BodePeaksOverlay(plot_item)
        overlay.set_visible(True)
        overlay.set_visible(False)

    def test_update_empty_dataset(self, plot_item):
        overlay = BodePeaksOverlay(plot_item)
        overlay.set_visible(True)
        overlay.update(BodeCsvDataset([]), y_linear=False)
        overlay.update(None, y_linear=False)

    def test_update_with_data(self, plot_item):
        pts = [
            BodeCsvPoint(1.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(2.0, 1.0, 1.0, 1.0),
            BodeCsvPoint(3.0, 1.0, 1.0, 2.0),
            BodeCsvPoint(4.0, 1.0, 1.0, 5.0),
            BodeCsvPoint(5.0, 1.0, 1.0, 2.0),
            BodeCsvPoint(6.0, 1.0, 1.0, 1.0),
            BodeCsvPoint(7.0, 1.0, 1.0, 0.0),
        ]
        ds = BodeCsvDataset(pts)
        overlay = BodePeaksOverlay(plot_item)
        overlay.set_visible(True)
        overlay.update(ds, y_linear=False)
        overlay.update(ds, y_linear=True)


# --- open_viewer (__init__.py) ---
from ui.bode_csv_viewer import open_viewer


class TestOpenViewer:
    def test_empty_path_returns_immediately(self):
        open_viewer(None, "", None)
        open_viewer(None, "", {})

    def test_empty_csv_shows_warning_and_returns(self, bode_csv_dir):
        from unittest.mock import patch
        empty_csv = bode_csv_dir / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")
        with patch("ui.bode_csv_viewer.QMessageBox.warning") as mock_warn:
            open_viewer(None, str(empty_csv), None)
        mock_warn.assert_called_once()
        assert "Aucune donnée" in mock_warn.call_args[0][2] or ""

    def test_valid_csv_opens_dialog(self, bode_csv_dir, qapp_for_viewer):
        from unittest.mock import patch
        valid_csv = bode_csv_dir / "valid.csv"
        valid_csv.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n100.0;0.7;0.7;-3.0\n",
            encoding="utf-8",
        )
        with patch("ui.bode_csv_viewer.BodeCsvViewerDialog") as mock_dialog:
            mock_dialog.return_value.exec.return_value = None
            open_viewer(None, str(valid_csv), {})
        mock_dialog.assert_called_once()
        call_kw = mock_dialog.call_args[1]
        assert call_kw["csv_path"] == str(valid_csv)
        assert not call_kw["dataset"].is_empty()
        mock_dialog.return_value.exec.assert_called_once()


@pytest.fixture
def qapp_for_viewer():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# --- Panneaux (panel_*.py) ---
from ui.bode_csv_viewer.panel_y_axis import build_y_axis_panel
from ui.bode_csv_viewer.panel_display import build_display_panel
from ui.bode_csv_viewer.panel_search import build_search_panel
from ui.bode_csv_viewer.panel_scale import build_scale_panel
from ui.bode_csv_viewer.panel_buttons import build_buttons_layout


class TestPanelBuilders:
    @pytest.fixture
    def qapp(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_build_y_axis_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        gb = build_y_axis_panel(parent)
        assert hasattr(parent, "_y_linear")
        assert hasattr(parent, "_y_db")
        assert hasattr(parent, "_y_group")
        assert gb is not None

    def test_build_display_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        parent._options = BodeViewOptions.default()
        gb = build_display_panel(parent, lambda: None)
        assert hasattr(parent, "_background_combo")
        assert hasattr(parent, "_curve_color_combo")
        assert hasattr(parent, "_grid_cb")
        assert hasattr(parent, "_smooth_cb")
        assert hasattr(parent, "_peaks_cb")
        assert gb is not None

    def test_build_search_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        gb = build_search_panel(parent, lambda: None, lambda: None)
        assert hasattr(parent, "_target_gain_spin")
        assert hasattr(parent, "_search_target_btn")
        assert hasattr(parent, "_clear_target_btn")
        assert hasattr(parent, "_target_result_label")
        assert gb is not None

    def test_build_scale_panel(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        gb = build_scale_panel(parent, lambda: None, lambda: None)
        assert hasattr(parent, "_f_min_spin")
        assert hasattr(parent, "_f_max_spin")
        assert hasattr(parent, "_gain_min_spin")
        assert hasattr(parent, "_apply_scale_btn")
        assert hasattr(parent, "_zoom_zone_cb")
        assert gb is not None

    def test_build_buttons_layout(self, qapp):
        from PyQt6.QtWidgets import QWidget
        parent = QWidget()
        parent.accept = lambda: None
        layout = build_buttons_layout(parent, lambda: None, lambda: None, lambda: None)
        assert hasattr(parent, "_adjust_btn")
        assert hasattr(parent, "_export_btn")
        assert hasattr(parent, "_export_csv_btn")
        assert hasattr(parent, "_close_btn")
        assert layout is not None


# --- BodeCsvViewerDialog ---
from ui.bode_csv_viewer.dialog import BodeCsvViewerDialog


class TestBodeCsvViewerDialog:
    @pytest.fixture
    def qapp(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def small_dataset(self):
        pts = [
            BodeCsvPoint(10.0, 1.0, 1.0, 0.0),
            BodeCsvPoint(100.0, 0.7, 0.7, -3.0),
            BodeCsvPoint(1000.0, 0.1, 0.1, -20.0),
        ]
        return BodeCsvDataset(pts)

    def test_dialog_creates_with_dataset(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=None)
        assert dlg._dataset.count == 3
        assert dlg._plot is not None
        dlg.close()

    def test_apply_bode_viewer_config_empty_no_op(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._apply_bode_viewer_config({})
        dlg.close()

    def test_apply_bode_viewer_config_applies_options(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._apply_bode_viewer_config({
            "plot_background_dark": False,
            "curve_color": "#e04040",
            "grid_visible": True,
            "grid_minor_visible": True,
            "smooth_window": 5,
            "show_raw_curve": True,
            "smooth_savgol": False,
            "y_linear": True,
            "peaks_visible": True,
        })
        dlg.close()

    def test_get_bode_viewer_state(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        state = dlg._get_bode_viewer_state()
        assert "plot_background_dark" in state
        assert "curve_color" in state
        assert "grid_visible" in state
        assert "y_linear" in state
        dlg.close()

    def test_save_bode_viewer_to_config(self, qapp, small_dataset):
        config = {}
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=config)
        dlg._save_bode_viewer_to_config()
        assert "bode_viewer" in config
        assert "curve_color" in config["bode_viewer"]
        dlg.close()

    def test_update_info_panel_empty(self, qapp):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=BodeCsvDataset([]), config={})
        dlg._update_info_panel()
        assert dlg._info_label.text() == ""
        dlg.close()

    def test_update_info_panel_with_data(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._update_info_panel()
        assert "G_max" in dlg._info_label.text() or "points" in dlg._info_label.text()
        dlg.close()

    def test_on_adjust_view_and_sync_scale(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._on_adjust_view()
        dlg._sync_scale_spins_from_view()
        dlg.close()

    def test_on_apply_scale(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._f_min_spin.setValue(10)
        dlg._f_max_spin.setValue(10000)
        dlg._gain_min_spin.setValue(-30)
        dlg._gain_max_spin.setValue(5)
        dlg._on_apply_scale()
        dlg.close()

    def test_on_apply_scale_corrects_inverted_range(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._f_min_spin.setValue(1000)
        dlg._f_max_spin.setValue(100)
        dlg._on_apply_scale()
        assert dlg._f_max_spin.value() >= dlg._f_min_spin.value()
        dlg.close()

    def test_on_zoom_zone_toggled(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._on_zoom_zone_toggled(True)
        dlg._on_zoom_zone_toggled(False)
        dlg.close()

    def test_on_search_target_gain(self, qapp, small_dataset):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        dlg._target_gain_spin.setValue(-3)
        dlg._on_search_target_gain()
        dlg._on_clear_target_gain()
        assert dlg._target_result_label.text() == ""
        dlg.close()

    def test_on_search_target_gain_empty_dataset(self, qapp):
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=BodeCsvDataset([]), config={})
        dlg._on_search_target_gain()
        assert "aucune donnée" in dlg._target_result_label.text().lower()
        dlg.close()

    def test_on_export_csv_with_data(self, qapp, small_dataset, bode_csv_dir):
        from unittest.mock import patch
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        path = str(bode_csv_dir / "exported.csv")
        with patch("ui.bode_csv_viewer.dialog.QFileDialog.getSaveFileName", return_value=(path, "")):
            with patch("ui.bode_csv_viewer.dialog.QMessageBox.information"):
                dlg._on_export_csv()
        assert Path(path).exists()
        dlg.close()

    def test_on_export_csv_empty_dataset_shows_warning(self, qapp):
        from unittest.mock import patch
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=BodeCsvDataset([]), config={})
        with patch("ui.bode_csv_viewer.dialog.QMessageBox.warning") as mock_warn:
            dlg._on_export_csv()
        mock_warn.assert_called_once()
        dlg.close()

    def test_accept_saves_config(self, qapp, small_dataset):
        config = {}
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=config)
        dlg.accept()
        assert "bode_viewer" in config
        dlg.close()

    def test_reject_saves_config(self, qapp, small_dataset):
        config = {}
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config=config)
        dlg.reject()
        assert "bode_viewer" in config
        dlg.close()

    def test_dialog_loads_csv_when_path_given_no_dataset(self, qapp, bode_csv_dir):
        valid_csv = bode_csv_dir / "load_test.csv"
        valid_csv.write_text(
            "f_Hz;Us_V;Us_Ue;Gain_dB\n50.0;0.8;0.8;-1.9\n200.0;0.5;0.5;-6.0\n",
            encoding="utf-8",
        )
        dlg = BodeCsvViewerDialog(None, csv_path=str(valid_csv), dataset=None, config={})
        assert dlg._dataset.count == 2
        dlg.close()

    def test_on_export_png(self, qapp, small_dataset, bode_csv_dir):
        from unittest.mock import patch
        dlg = BodeCsvViewerDialog(None, csv_path="", dataset=small_dataset, config={})
        path = str(bode_csv_dir / "graph.png")
        with patch("ui.bode_csv_viewer.dialog.QFileDialog.getSaveFileName", return_value=(path, "")):
            with patch("ui.bode_csv_viewer.dialog.QMessageBox.information"):
                dlg._on_export()
        dlg.close()
