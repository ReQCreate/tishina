# -*- coding: utf-8 -*-
"""5-полосный эквалайзер."""

from __future__ import annotations

import numpy as np

from .base import AudioModule, ProcessContext
from .biquad import Biquad, high_shelf, highpass, low_shelf, peaking


class EqModule(AudioModule):
    name = "eq"

    def __init__(
        self,
        sample_rate: int = 48_000,
        hp_hz: float = 80.0,
        low_gain: float = 0.0,
        mid_gain: float = 0.0,
        presence_gain: float = 0.0,
        high_gain: float = 0.0,
    ) -> None:
        super().__init__(enabled=True)
        self.sample_rate = sample_rate
        self.hp_hz = hp_hz
        self.low_gain = low_gain
        self.mid_gain = mid_gain
        self.presence_gain = presence_gain
        self.high_gain = high_gain
        self._build()

    def _build(self) -> None:
        fs = self.sample_rate
        self._hp = Biquad(*highpass(fs, max(20.0, min(self.hp_hz, fs / 2.0 - 100.0))))
        self._low = Biquad(*low_shelf(fs, 200.0, self.low_gain))
        self._mid = Biquad(*peaking(fs, 1000.0, self.mid_gain, q=1.0))
        self._presence = Biquad(*peaking(fs, 3000.0, self.presence_gain, q=1.0))
        self._high = Biquad(*high_shelf(fs, 10_000.0, self.high_gain))

    def set_params(self, **params) -> None:
        super().set_params(**params)
        self._build()

    def reset(self) -> None:
        for band in (self._hp, self._low, self._mid, self._presence, self._high):
            band.reset()

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        if not self.enabled:
            return frame
        out = self._hp.process(frame)
        if abs(self.low_gain) > 0.01:
            out = self._low.process(out)
        if abs(self.mid_gain) > 0.01:
            out = self._mid.process(out)
        if abs(self.presence_gain) > 0.01:
            out = self._presence.process(out)
        if abs(self.high_gain) > 0.01:
            out = self._high.process(out)
        return out.astype(np.float32)
