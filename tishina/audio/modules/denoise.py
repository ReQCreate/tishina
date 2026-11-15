# -*- coding: utf-8 -*-
"""RNNoise через ctypes.

DLL лежит в tishina/vendor/rnnoise.dll. Мы не импортируем пакет pyrnnoise
(он тянет audiolab/matplotlib), а грузим DLL напрямую.
"""

from __future__ import annotations

import ctypes
import importlib.util
import sys
from pathlib import Path

import numpy as np

from ...config import PACKAGE_DIR, RNNOISE_DLL
from .base import AudioModule, ProcessContext


def _candidate_paths():
    yield RNNOISE_DLL
    yield PACKAGE_DIR / "vendor" / "rnnoise.dll"
    if getattr(sys, "_MEIPASS", None):
        yield Path(sys._MEIPASS) / "tishina" / "vendor" / "rnnoise.dll"
    try:
        spec = importlib.util.find_spec("pyrnnoise")
        if spec and spec.origin:
            yield Path(spec.origin).parent / "rnnoise.dll"
    except Exception:
        pass


class RNNoiseDenoiser:
    """Тонкая обёртка над C-API RNNoise."""

    def __init__(self) -> None:
        self.available = False
        self.error = ""
        self.frame_size = 480
        self._lib = None
        self._state = None
        self._load()

    def _load(self) -> None:
        last_error = ""
        for path in _candidate_paths():
            if not path.exists():
                continue
            try:
                lib = ctypes.CDLL(str(path))
                lib.rnnoise_create.argtypes = [ctypes.c_void_p]
                lib.rnnoise_create.restype = ctypes.c_void_p
                lib.rnnoise_destroy.argtypes = [ctypes.c_void_p]
                lib.rnnoise_process_frame.argtypes = [
                    ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                ]
                lib.rnnoise_process_frame.restype = ctypes.c_float
                lib.rnnoise_get_frame_size.restype = ctypes.c_int

                state = lib.rnnoise_create(None)
                if not state:
                    raise RuntimeError("rnnoise_create() вернул NULL")

                self._lib = lib
                self._state = state
                self.frame_size = int(lib.rnnoise_get_frame_size())
                self._in_f32 = np.zeros(self.frame_size, dtype=np.float32)
                self._out_f32 = np.zeros(self.frame_size, dtype=np.float32)
                self._out_float = np.zeros(self.frame_size, dtype=np.float32)
                self._in_ptr = self._in_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                self._out_ptr = self._out_f32.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
                self.available = True
                self.error = ""
                return
            except Exception as exc:  # noqa: BLE001
                last_error = f"{path}: {exc}"

        self.error = last_error or "rnnoise.dll не найден"

    def process(self, frame: np.ndarray) -> tuple[np.ndarray, float]:
        if not self.available or self._lib is None or self._state is None:
            return frame, 0.0

        n = min(int(frame.size), self.frame_size)
        if n <= 0:
            return frame, 0.0

        # RNNoise ожидает float32 со значениями в диапазоне int16.
        np.clip(frame[:n], -1.0, 1.0, out=self._in_f32[:n])
        self._in_f32[:n] *= 32767.0
        if n < self.frame_size:
            self._in_f32[n:] = 0.0

        vad = float(self._lib.rnnoise_process_frame(self._state, self._out_ptr, self._in_ptr))

        np.multiply(self._out_f32[:n], 1.0 / 32768.0, out=self._out_float[:n])
        return self._out_float[:n], max(0.0, min(1.0, vad))

    def reset(self) -> None:
        if self._lib is None:
            return
        if self._state:
            self._lib.rnnoise_destroy(self._state)
            self._state = None
        if self.available:
            self._state = self._lib.rnnoise_create(None)

    def close(self) -> None:
        if self._lib is not None and self._state:
            self._lib.rnnoise_destroy(self._state)
            self._state = None
        self.available = False


class DenoiseModule(AudioModule):
    name = "denoise"

    def __init__(self, mix: float = 0.75, sample_rate: int = 48_000) -> None:
        super().__init__(enabled=True)
        self.sample_rate = sample_rate
        self.mix = mix
        self.denoiser = RNNoiseDenoiser()
        self.last_vad = 0.0
        self.last_error = self.denoiser.error

    @property
    def available(self) -> bool:
        return self.denoiser.available

    def process(self, frame: np.ndarray, ctx: ProcessContext) -> np.ndarray:
        if not self.enabled or not self.denoiser.available:
            ctx.vad = 0.0
            return frame

        wet, vad = self.denoiser.process(frame)
        ctx.vad = vad
        self.last_vad = vad
        mix = float(np.clip(self.mix, 0.0, 1.0))
        if mix >= 0.999:
            return wet
        if mix <= 0.001:
            return frame
        return (frame * (1.0 - mix) + wet * mix).astype(np.float32)

    def reset(self) -> None:
        self.denoiser.reset()
        self.last_vad = 0.0
