# -*- coding: utf-8 -*-
"""Генерация тестового WAV: тон + шум + наводка 50 Гц."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 48_000


def make_test_wav(path: Path, seconds: float = 5.0, noise_db: float = -38.0) -> None:
    rng = np.random.default_rng(42)
    t = np.arange(int(seconds * SAMPLE_RATE), dtype=np.float64) / SAMPLE_RATE

    # Похожий на голос тон с амплитудной модуляцией.
    voice = 0.22 * np.sin(2.0 * np.pi * 180.0 * t)
    voice *= 0.65 + 0.35 * np.sin(2.0 * np.pi * 3.2 * t)
    voice += 0.06 * np.sin(2.0 * np.pi * 360.0 * t)

    noise = rng.normal(0.0, 1.0, t.size)
    noise *= 10.0 ** (noise_db / 20.0) / max(float(np.sqrt(np.mean(noise**2))), 1e-9)
    hum = 0.02 * np.sin(2.0 * np.pi * 50.0 * t)

    audio = np.clip(voice + noise + hum, -1.0, 1.0)
    wavfile.write(path, SAMPLE_RATE, (audio * 32767.0).astype(np.int16))
    print(f"Записан {path}: {seconds:.1f} с, шум {noise_db:.1f} dBFS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, nargs="?", default=Path("test_input.wav"))
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--noise-db", type=float, default=-38.0)
    args = parser.parse_args()
    make_test_wav(args.output, args.seconds, args.noise_db)


if __name__ == "__main__":
    main()
