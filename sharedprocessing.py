"""shared/processing.py — 2 Jenis Data Processing untuk StoveWatch."""

import numpy as np


# DATA PROCESSING 1: Algoritma Sinyal (RMS & Rolling Z-Score)
# Dipakai untuk mendeteksi suara desis gas / gejolak masak kompor

class StoveNoiseAnalyzer:
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.history = []

    def compute_rms(self, audio_samples: np.ndarray) -> float:
        """Menghitung intensitas suara energi Root Mean Square (RMS)."""
        if len(audio_samples) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(audio_samples))))

    def compute_z_score(self, current_rms: float) -> tuple[float, bool]:
        """Algoritma Statistical Outlier (Z-Score) untuk mendeteksi lonjakan kompor."""
        self.history.append(current_rms)
        if len(self.history) > self.window_size:
            self.history.pop(0)

        if len(self.history) < 5:
            return 0.0, False

        mean = np.mean(self.history)
        std = np.std(self.history) + 1e-6
        z_score = float((current_rms - mean) / std)
        is_boiling = z_score > 1.8  # Deteksi aktivitas masak aktif
        return z_score, is_boiling


# DATA PROCESSING 2: Edge-AI Presence Heuristic / Timer
# Dipakai untuk mendeteksi keberadaan orang di depan kompor

class PresenceTimeDecay:
    def __init__(self, max_idle_sec: int = 15):
        self.max_idle_sec = max_idle_sec
        self.seconds_unattended = 0

    def update(self, person_detected: bool, delta_time: float = 1.0) -> dict:
        """Algoritma state-machine & akumulasi durasi kompor ditinggal."""
        if person_detected:
            self.seconds_unattended = 0
            state = "ATTENDED"
        else:
            self.seconds_unattended += delta_time
            state = "UNATTENDED" if self.seconds_unattended >= self.max_idle_sec else "WARNING"

        return {
            "state": state,
            "idle_seconds": round(self.seconds_unattended, 1),
            "is_danger": self.seconds_unattended >= self.max_idle_sec
        }