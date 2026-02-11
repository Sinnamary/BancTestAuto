"""Tests du view state (BodeViewOptions)."""
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
