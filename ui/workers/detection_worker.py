"""
Thread pour la détection des équipements (multimètre OWON, générateur FY6900).
Évite de bloquer l'UI. Utilisé par MainWindow (barre Charger config) et DeviceDetectionDialog.

REMOVE_AFTER_PHASE5: Worker tuple (m_port, m_baud, g_port, g_baud, log). Remplacer par
un worker basé sur core.detection.run_detection et BenchDetectionResult (4 équipements),
puis supprimer ce fichier. Voir docs/DEVELOPPEMENT.md.
"""
from PyQt6.QtCore import QThread, pyqtSignal

try:
    from core.device_detection import detect_devices
except ImportError:
    detect_devices = None


class DetectionWorker(QThread):
    """Lance detect_devices() et émet le résultat (ports, débits, lignes de log)."""
    result = pyqtSignal(object, object, object, object, object)  # m_port, m_baud, g_port, g_baud, log_lines

    def run(self):
        if detect_devices is None:
            self.result.emit(None, None, None, None, [])
            return
        m_port, m_baud, g_port, g_baud, log_lines = detect_devices()
        self.result.emit(m_port, m_baud, g_port, g_baud, log_lines)
