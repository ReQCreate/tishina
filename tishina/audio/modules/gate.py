# -*- coding: utf-8 -*-
"""Шумовой гейт с поддержкой VAD.

Гейт работает на уровне кадра (10 мс): считает RMS, решает, открыт ли гейт,
и плавно интерполирует усиление внутри кадра. Это заметно дешевле
пошагового Python-цикла и для голоса звучит достаточно гладко.
"""

from __future__ import annotations

import math

import numpy as np

from .base import AudioModule, ProcessContext


class GateModule(AudioModule):
    name = "gate"

    def __init__(
        self,
        sample_rate: int = 48_000,
        threshold_db: float = -42.0,
        attack_ms: float = 5.0,
        release_ms: float = 150.0,
        hold_ms: float = 50.0,
        range_db: float = -60.0,
        use_vad: bool = True,
        vad_threshold: float = 0.3,
    ) -> None:
        super().__init__(enabled=True)
        self.sample_rate = sample_rate
        self.threshold_db = threshold_db
        self.attack_ms = attack_ms
        self.release_ms = release_ms
        self.hold_ms = hold_ms
        self.range_db = range_db
        self.use_vad = use_vad
        self.vad_threshold = vad_threshold
        self._gain = 1.0
        self._hold = 0.0
        self._range = 10.0 ** (range_db / 20.0)
        self._update()

    def _update(self) -> None:
        self._range = 10.0 ** (self.range_db / 20.0)

    def set_params(self, **params) -> None:
        super().set_params(**params)
        self._update()

    def reset(self) -> None:
        self._gain = 1.0
        self._hold = 0.0

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        if not self.enabled or frame.size == 0:
            return frame

        dt = frame.size / float(self.sample_rate)
        attack = math.exp(-dt / max(self.attack_ms / 1000.0, 1e-4))
        release = math.exp(-dt / max(self.release_ms / 1000.0, 1e-4))

        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)))
        level_db = 20.0 * math.log10(rms + 1e-12)
        is_open = level_db > self.threshold_db or (self.use_vad and ctx.vad >= self.vad_threshold)

        if is_open:
            self._hold = max(0.0, self.hold_ms / 1000.0)
        elif self._hold > 0.0:
            self._hold = max(0.0, self._hold - dt)
            is_open = True

        target = 1.0 if is_open else self._range
        previous = self._gain
        coefficient = attack if target > previous else release
        current = coefficient * previous + (1.0 - coefficient) * target

        if abs(previous - current) < 1e-6:
            self._gain = current
            if abs(current - 1.0) < 1e-6:
                return frame
            return (frame * current).astype(np.float32)

        curve = np.linspace(previous, current, frame.size, dtype=np.float32)
        self._gain = current
        return (frame * curve).astype(np.float32)
