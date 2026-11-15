# -*- coding: utf-8 -*-
"""Компрессор с мягким коленом.

Уровень и усиление считаются на кадр (10 мс), внутри кадра усиление
интерполируется. Это компромисс между качеством и нагрузкой CPU.
"""

from __future__ import annotations

import math

import numpy as np

from .base import AudioModule, ProcessContext


class CompressorModule(AudioModule):
    name = "compressor"

    def __init__(
        self,
        sample_rate: int = 48_000,
        threshold_db: float = -18.0,
        ratio: float = 2.5,
        attack_ms: float = 10.0,
        release_ms: float = 100.0,
        knee_db: float = 6.0,
        makeup_db: float = 4.0,
    ) -> None:
        super().__init__(enabled=True)
        self.sample_rate = sample_rate
        self.threshold_db = threshold_db
        self.ratio = ratio
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.knee_db = knee_db
        self.makeup_db = makeup_db
        self._gain = 1.0
        self.reduction_db = 0.0
        self._update()

    def _update(self) -> None:
        self._makeup = 10.0 ** (self.makeup_db / 20.0)

    def set_params(self, **params) -> None:
        super().set_params(**params)
        self._update()

    def reset(self) -> None:
        self._gain = 1.0
        self.reduction_db = 0.0

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        if not self.enabled or self.ratio <= 1.001 or frame.size == 0:
            return frame

        dt = frame.size / float(self.sample_rate)
        attack = math.exp(-dt / max(self.attack_ms / 1000.0, 1e-4))
        release = math.exp(-dt / max(self.release_ms / 1000.0, 1e-4))

        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        level_db = 20.0 * math.log10(rms + 1e-12)
        over = level_db - self.threshold_db
        ratio = max(1.0, self.ratio)
        knee = max(0.001, self.knee_db)
        slope = 1.0 - 1.0 / ratio

        if over <= -knee / 2.0:
            reduction = 0.0
        elif over >= knee / 2.0:
            reduction = -over * slope
        else:
            t = over + knee / 2.0
            reduction = -slope * (t * t) / (2.0 * knee)

        target = 10.0 ** ((reduction + self.makeup_db) / 20.0)
        previous = self._gain
        coefficient = attack if target < previous else release
        current = coefficient * previous + (1.0 - coefficient) * target

        if abs(previous - current) < 1e-6:
            self._gain = current
            if abs(current - 1.0) < 1e-6:
                return frame
            return (frame * current).astype(np.float32)

        curve = np.linspace(previous, current, frame.size, dtype=np.float32)
        self._gain = current
        self.reduction_db = 20.0 * math.log10(max(current, 1e-9)) - self.makeup_db
        return (frame * curve).astype(np.float32)
