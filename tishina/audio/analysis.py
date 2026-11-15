# -*- coding: utf-8 -*-
"""Метры и приблизительная лаудность (ITU-R BS.1770)."""

from __future__ import annotations

import math
import threading

import numpy as np

from .modules.biquad import Biquad

# Коэффициенты K-weighting для 48 кГц (BS.1770-4).
_K_SHELF_B = (1.53512485958697, -2.69169618940638, 1.19839281085285)
_K_SHELF_A = (1.0, -1.69065929318241, 0.73248077421585)
_K_HP_B = (1.0, -2.0, 1.0)
_K_HP_A = (1.0, -1.99004745483398, 0.99007225036621)


class AudioAnalyzer:
    """Считает уровни, шумовой пол, VAD и короткую лаудность."""

    def __init__(self, sample_rate: int = 48_000) -> None:
        self.sample_rate = sample_rate
        self._lock = threading.Lock()

        self.input_peak_db = -90.0
        self.input_rms_db = -90.0
        self.output_peak_db = -90.0
        self.output_rms_db = -90.0
        self.noise_floor_db = -60.0
        self.vad = 0.0
        self.lufs = -70.0
        self._noise_initialized = False

        self._k1 = Biquad(_K_SHELF_B, _K_SHELF_A)
        self._k2 = Biquad(_K_HP_B, _K_HP_A)
        self._lufs_len = max(1, int(0.4 * sample_rate))
        self._lufs_buf = np.zeros(self._lufs_len, dtype=np.float32)
        self._lufs_idx = 0
        self._lufs_filled = 0

    @staticmethod
    def _db(value: float) -> float:
        return 20.0 * math.log10(max(float(value), 1e-9))

    def process_input(self, frame: np.ndarray, vad: float) -> None:
        frame = np.asarray(frame, dtype=np.float32)
        peak = float(np.max(np.abs(frame))) if frame.size else 0.0
        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2))) if frame.size else 0.0
        peak_db = self._db(peak)
        rms_db = self._db(rms)

        with self._lock:
            self.input_peak_db = max(peak_db, self.input_peak_db - 0.8)
            self.input_rms_db = 0.7 * self.input_rms_db + 0.3 * rms_db
            self.vad = 0.8 * self.vad + 0.2 * float(vad)

            if vad < 0.2 and rms_db > -85.0:
                if not self._noise_initialized:
                    self.noise_floor_db = rms_db
                    self._noise_initialized = True
                else:
                    self.noise_floor_db = 0.995 * self.noise_floor_db + 0.005 * rms_db

    def process_output(self, frame: np.ndarray) -> None:
        frame = np.asarray(frame, dtype=np.float32)
        peak = float(np.max(np.abs(frame))) if frame.size else 0.0
        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2))) if frame.size else 0.0

        weighted = self._k1.process(frame)
        weighted = self._k2.process(weighted)

        with self._lock:
            self.output_peak_db = max(self._db(peak), self.output_peak_db - 0.8)
            self.output_rms_db = 0.7 * self.output_rms_db + 0.3 * self._db(rms)

            n = weighted.size
            for i in range(n):
                self._lufs_buf[self._lufs_idx] = weighted[i]
                self._lufs_idx = (self._lufs_idx + 1) % self._lufs_len
                if self._lufs_filled < self._lufs_len:
                    self._lufs_filled += 1

            if self._lufs_filled:
                if self._lufs_filled < self._lufs_len:
                    chunk = self._lufs_buf[: self._lufs_filled]
                else:
                    chunk = self._lufs_buf
                mean_square = float(np.mean(chunk.astype(np.float64) ** 2))
                self.lufs = -0.691 + 10.0 * math.log10(mean_square + 1e-12)

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return {
                "input_peak_db": self.input_peak_db,
                "input_rms_db": self.input_rms_db,
                "output_peak_db": self.output_peak_db,
                "output_rms_db": self.output_rms_db,
                "noise_floor_db": self.noise_floor_db,
                "vad": self.vad,
                "lufs": self.lufs,
            }

    def reset(self) -> None:
        with self._lock:
            self.input_peak_db = -90.0
            self.input_rms_db = -90.0
            self.output_peak_db = -90.0
            self.output_rms_db = -90.0
            self.noise_floor_db = -60.0
            self.vad = 0.0
            self.lufs = -70.0
            self._noise_initialized = False
            self._lufs_idx = 0
            self._lufs_filled = 0
            self._lufs_buf.fill(0.0)
        self._k1.reset()
        self._k2.reset()
