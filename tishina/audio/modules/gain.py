# -*- coding: utf-8 -*-
"""Выходной gain и mute."""

from __future__ import annotations

import numpy as np

from .base import AudioModule, ProcessContext


class GainModule(AudioModule):
    name = "gain"

    def __init__(self, gain_db: float = 0.0, mute: bool = False) -> None:
        super().__init__(enabled=True)
        self.gain_db = gain_db
        self.mute = mute
        self._update()

    def _update(self) -> None:
        self._gain = 10.0 ** (self.gain_db / 20.0)

    def set_params(self, **params) -> None:
        super().set_params(**params)
        self._update()

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        if not self.enabled:
            return frame
        if self.mute:
            return np.zeros_like(frame)
        if abs(self._gain - 1.0) < 1e-6:
            return frame
        return (frame * self._gain).astype(np.float32)
