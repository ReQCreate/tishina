# -*- coding: utf-8 -*-
"""Биквады и коэффициенты RBJ."""

from __future__ import annotations

import math

import numpy as np
from scipy.signal import lfilter


class Biquad:
    """Биквад с сохранением состояния между кадрами.

    Фильтрация выполняется в C через scipy.signal.lfilter: это в разы
    быстрее пошагового Python-цикла и важно для реального времени.
    """

    __slots__ = ("b", "a", "zi")

    def __init__(self, b, a) -> None:
        b0, b1, b2 = (float(v) for v in b)
        a0, a1, a2 = (float(v) for v in a)
        if a0 == 0.0:
            raise ValueError("a0 must not be zero")
        self.b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
        self.a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)
        self.zi = np.zeros(2, dtype=np.float64)

    def reset(self) -> None:
        self.zi.fill(0.0)

    def process(self, x: np.ndarray) -> np.ndarray:
        y, self.zi = lfilter(self.b, self.a, x, zi=self.zi)
        return y.astype(np.float32, copy=False)


def peaking(fs: float, f0: float, gain_db: float, q: float = 1.0):
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * f0 / fs
    alpha = math.sin(w0) / (2.0 * q)
    cosw = math.cos(w0)
    b = [1.0 + alpha * a, -2.0 * cosw, 1.0 - alpha * a]
    den = [1.0 + alpha / a, -2.0 * cosw, 1.0 - alpha / a]
    return b, den


def low_shelf(fs: float, f0: float, gain_db: float, slope: float = 1.0):
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * f0 / fs
    cosw = math.cos(w0)
    sinw = math.sin(w0)
    alpha = sinw / 2.0 * math.sqrt((a + 1.0 / a) * (1.0 / slope - 1.0) + 2.0)
    sa = 2.0 * math.sqrt(a) * alpha
    b = [
        a * ((a + 1.0) - (a - 1.0) * cosw + sa),
        2.0 * a * ((a - 1.0) - (a + 1.0) * cosw),
        a * ((a + 1.0) - (a - 1.0) * cosw - sa),
    ]
    den = [
        (a + 1.0) + (a - 1.0) * cosw + sa,
        -2.0 * ((a - 1.0) + (a + 1.0) * cosw),
        (a + 1.0) + (a - 1.0) * cosw - sa,
    ]
    return b, den


def high_shelf(fs: float, f0: float, gain_db: float, slope: float = 1.0):
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * f0 / fs
    cosw = math.cos(w0)
    sinw = math.sin(w0)
    alpha = sinw / 2.0 * math.sqrt((a + 1.0 / a) * (1.0 / slope - 1.0) + 2.0)
    sa = 2.0 * math.sqrt(a) * alpha
    b = [
        a * ((a + 1.0) + (a - 1.0) * cosw + sa),
        -2.0 * a * ((a - 1.0) + (a + 1.0) * cosw),
        a * ((a + 1.0) + (a - 1.0) * cosw - sa),
    ]
    den = [
        (a + 1.0) - (a - 1.0) * cosw + sa,
        2.0 * ((a - 1.0) - (a + 1.0) * cosw),
        (a + 1.0) - (a - 1.0) * cosw - sa,
    ]
    return b, den


def highpass(fs: float, f0: float, q: float = 0.70710678):
    w0 = 2.0 * math.pi * f0 / fs
    cosw = math.cos(w0)
    sinw = math.sin(w0)
    alpha = sinw / (2.0 * q)
    b = [(1.0 + cosw) / 2.0, -(1.0 + cosw), (1.0 + cosw) / 2.0]
    den = [1.0 + alpha, -2.0 * cosw, 1.0 - alpha]
    return b, den
