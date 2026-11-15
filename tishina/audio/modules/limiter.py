# -*- coding: utf-8 -*-
"""Лимитер с lookahead.

Выход задерживается на lookahead, а усиление рассчитывается по пику
текущего кадра. Атака успевает отработать до прихода пика.
"""

from __future__ import annotations

import math

import numpy as np

from .base import AudioModule, ProcessContext


class LimiterModule(AudioModule):
    name = "limiter"

    def __init__(
        self,
        sample_rate: int = 48_000,
        ceiling_db: float = -1.0,
        lookahead_ms: float = 5.0,
        release_ms: float = 50.0,
    ) -> None:
        super().__init__(enabled=True)
        self.sample_rate = sample_rate
        self.ceiling_db = ceiling_db
        self.lookahead_ms = lookahead_ms
        self.release_ms = release_ms
        self._update()

    def _update(self) -> None:
        self._ceiling = 10.0 ** (self.ceiling_db / 20.0)
        self._lookahead = max(1, int(self.sample_rate * self.lookahead_ms / 1000.0))
        self._buffer = np.zeros(self._lookahead, dtype=np.float32)
        self._gain = 1.0
        self.reduction_db = 0.0

    def set_params(self, **params) -> None:
        super().set_params(**params)
        self._update()

    def reset(self) -> None:
        self._buffer.fill(0.0)
        self._gain = 1.0
        self.reduction_db = 0.0

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        if not self.enabled:
            self._buffer.fill(0.0)
            return frame
        if frame.size == 0:
            return frame

        # Задержка на lookahead.
        combined = np.concatenate((self._buffer, frame))
        delayed = combined[: frame.size]
        self._buffer = combined[-self._lookahead :].copy()

        peak = float(np.max(np.abs(frame)))
        target = 1.0 if peak <= self._ceiling else self._ceiling / (peak + 1e-12)
        previous = self._gain
        n = frame.size

        if target < previous - 1e-6:
            attack_samples = min(n, max(1, self._lookahead))
            curve = np.empty(n, dtype=np.float32)
            curve[:attack_samples] = np.linspace(previous, target, attack_samples, dtype=np.float32)
            curve[attack_samples:] = target
            self._gain = target
        elif target > previous + 1e-6:
            dt = n / float(self.sample_rate)
            release = math.exp(-dt / max(self.release_ms / 1000.0, 1e-4))
            current = release * previous + (1.0 - release) * target
            curve = np.linspace(previous, current, n, dtype=np.float32)
            self._gain = current
        else:
            curve = np.full(n, previous, dtype=np.float32)
            self._gain = previous

        out = delayed * curve
        np.clip(out, -self._ceiling, self._ceiling, out=out)
        self.reduction_db = 20.0 * math.log10(max(self._gain, 1e-9))
        return out.astype(np.float32, copy=False)
