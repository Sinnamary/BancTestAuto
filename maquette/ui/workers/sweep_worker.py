"""
Thread pour le balayage en fréquence (banc filtre).
Exécute FilterTest.run_sweep() sans bloquer l'UI.
"""
from PyQt6.QtCore import QThread, pyqtSignal


class SweepWorker(QThread):
    """Lance le balayage et émet les points / progression / fin."""
    point_received = pyqtSignal(object, int, int)  # BodePoint, index, total
    progress = pyqtSignal(int, int)
    finished_sweep = pyqtSignal(list)  # list[BodePoint]
    error = pyqtSignal(str)
    stabilization_started = pyqtSignal()
    stabilization_ended = pyqtSignal()

    def __init__(self, filter_test):
        super().__init__()
        self._filter_test = filter_test

    def run(self):
        try:
            results = self._filter_test.run_sweep(
                on_point=lambda p, i, t: self.point_received.emit(p, i, t),
                on_progress=lambda i, t: self.progress.emit(i, t),
                on_stabilization_started=lambda: self.stabilization_started.emit(),
                on_stabilization_ended=lambda: self.stabilization_ended.emit(),
            )
            self.finished_sweep.emit(results)
        except Exception as e:
            self.error.emit(str(e))
