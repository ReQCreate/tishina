# -*- coding: utf-8 -*-
"""Аудио-цепочка обработки."""

from __future__ import annotations

from typing import Any

import numpy as np

from .modules.base import AudioModule, ProcessContext
from .modules.compressor import CompressorModule
from .modules.denoise import DenoiseModule
from .modules.eq import EqModule
from .modules.gain import GainModule
from .modules.gate import GateModule
from .modules.limiter import LimiterModule


class Chain:
    """Последовательность DSP-модулей."""

    def __init__(self, sample_rate: int = 48_000, preset: dict[str, Any] | None = None) -> None:
        self.sample_rate = sample_rate
        self.denoise = DenoiseModule(sample_rate=sample_rate)
        self.gate = GateModule(sample_rate=sample_rate)
        self.eq = EqModule(sample_rate=sample_rate)
        self.compressor = CompressorModule(sample_rate=sample_rate)
        self.limiter = LimiterModule(sample_rate=sample_rate)
        self.gain = GainModule()
        self.modules: list[AudioModule] = [
            self.denoise,
            self.gate,
            self.eq,
            self.compressor,
            self.limiter,
            self.gain,
        ]
        self.bypass = False
        self.last_vad = 0.0
        self.last_ctx = ProcessContext()

        if preset:
            self.apply_preset(preset)

    def module_by_name(self, name: str) -> AudioModule | None:
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def apply_preset(self, preset: dict[str, Any]) -> None:
        modules = preset.get("modules", {})
        for name, params in modules.items():
            module = self.module_by_name(name)
            if module is not None and isinstance(params, dict):
                module.set_params(**params)

    def process(self, frame: np.ndarray) -> np.ndarray:
        if self.bypass:
            self.last_vad = 0.0
            return frame.copy()

        ctx = ProcessContext()
        out = frame
        for module in self.modules:
            out = module.process(out, ctx)
        self.last_vad = ctx.vad
        self.last_ctx = ctx
        return out

    def reset(self) -> None:
        for module in self.modules:
            module.reset()
        self.last_vad = 0.0

    def set_bypass(self, value: bool) -> None:
        self.bypass = bool(value)

    def set_enabled(self, name: str, value: bool) -> None:
        module = self.module_by_name(name)
        if module is not None:
            module.enabled = bool(value)

    def to_preset(self, name: str = "Custom") -> dict[str, Any]:
        return {
            "name": name,
            "modules": {
                "denoise": {"enabled": self.denoise.enabled, "mix": self.denoise.mix},
                "gate": {
                    "enabled": self.gate.enabled,
                    "threshold_db": self.gate.threshold_db,
                    "attack_ms": self.gate.attack_ms,
                    "release_ms": self.gate.release_ms,
                    "hold_ms": self.gate.hold_ms,
                    "range_db": self.gate.range_db,
                    "use_vad": self.gate.use_vad,
                    "vad_threshold": self.gate.vad_threshold,
                },
                "eq": {
                    "enabled": self.eq.enabled,
                    "hp_hz": self.eq.hp_hz,
                    "low_gain": self.eq.low_gain,
                    "mid_gain": self.eq.mid_gain,
                    "presence_gain": self.eq.presence_gain,
                    "high_gain": self.eq.high_gain,
                },
                "compressor": {
                    "enabled": self.compressor.enabled,
                    "threshold_db": self.compressor.threshold_db,
                    "ratio": self.compressor.ratio,
                    "attack_ms": self.compressor.attack_ms,
                    "release_ms": self.compressor.release_ms,
                    "knee_db": self.compressor.knee_db,
                    "makeup_db": self.compressor.makeup_db,
                },
                "limiter": {
                    "enabled": self.limiter.enabled,
                    "ceiling_db": self.limiter.ceiling_db,
                    "lookahead_ms": self.limiter.lookahead_ms,
                    "release_ms": self.limiter.release_ms,
                },
                "gain": {"enabled": self.gain.enabled, "gain_db": self.gain.gain_db},
            },
        }
