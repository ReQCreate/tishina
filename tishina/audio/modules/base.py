# -*- coding: utf-8 -*-
"""Базовые интерфейсы DSP-модулей."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ProcessContext:
    """Данные, которые модули передают друг другу в пределах кадра."""

    vad: float = 0.0
    input_peak: float = 0.0
    input_rms: float = 0.0


class AudioModule:
    """Один модуль цепочки: получает кадр, возвращает кадр."""

    name = "module"

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        return frame

    def reset(self) -> None:
        pass

    def set_params(self, **params) -> None:
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
