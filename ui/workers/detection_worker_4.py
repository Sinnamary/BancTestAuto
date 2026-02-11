"""
Thread pour la détection des 4 équipements (core.detection.run_detection).
Émet BenchDetectionResult. Utilisé par DeviceDetectionDialog4 (Phase 2).
"""
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from core.detection import run_detection
    from core.equipment import bench_equipment_kinds
except ImportError:
    run_detection = None
    bench_equipment_kinds = None


class DetectionWorker4(QThread):
    """Lance run_detection(bench_equipment_kinds(), log_lines) et émet BenchDetectionResult."""

    result = pyqtSignal(object)  # BenchDetectionResult

    def run(self):
        if run_detection is None or bench_equipment_kinds is None:
            self.result.emit(None)
            return
        log_lines: list = []
        bench_result = run_detection(kinds=bench_equipment_kinds(), log_lines=log_lines)
        self.result.emit(bench_result)
