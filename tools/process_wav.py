# -*- coding: utf-8 -*-
"""Офлайн-обработка WAV через цепочку Тишины.

Пример:
    python tools/process_wav.py in.wav out.wav --preset Stream
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tishina.audio.chain import Chain  # noqa: E402
from tishina.config import BLOCK_SIZE, SAMPLE_RATE  # noqa: E402
from tishina.presets import load_preset  # noqa: E402


def read_mono_48k(path: Path) -> np.ndarray:
    sample_rate, data = wavfile.read(path)
    if data.dtype == np.uint8:
        data = (data.astype(np.float32) - 128.0) / 128.0
    elif data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.float32:
        data = data.astype(np.float32)
    else:
        data = data.astype(np.float32)

    if data.ndim == 2:
        data = data.mean(axis=1)

    if sample_rate != SAMPLE_RATE:
        gcd = math.gcd(int(sample_rate), SAMPLE_RATE)
        up = SAMPLE_RATE // gcd
        down = int(sample_rate) // gcd
        data = resample_poly(data, up, down).astype(np.float32)

    return np.ascontiguousarray(data, dtype=np.float32)


def rms_db(x: np.ndarray) -> float:
    if x.size == 0:
        return -90.0
    return 20.0 * math.log10(max(float(np.sqrt(np.mean(x.astype(np.float64) ** 2))), 1e-9))


def process(input_path: Path, output_path: Path, preset_name: str, bypass: bool) -> None:
    audio = read_mono_48k(input_path)
    if audio.size == 0:
        raise ValueError("Входной файл пустой")

    chain = Chain(sample_rate=SAMPLE_RATE)
    chain.apply_preset(load_preset(preset_name))
    chain.set_bypass(bypass)

    pad = (-audio.size) % BLOCK_SIZE
    if pad:
        audio = np.pad(audio, (0, pad))

    out = np.empty_like(audio)
    for start in range(0, audio.size, BLOCK_SIZE):
        frame = audio[start : start + BLOCK_SIZE]
        out[start : start + BLOCK_SIZE] = chain.process(frame)

    out = np.clip(out, -1.0, 1.0)
    wavfile.write(output_path, SAMPLE_RATE, (out * 32767.0).astype(np.int16))

    print(f"Вход:  {input_path}  RMS {rms_db(audio):.1f} dBFS  peak {np.max(np.abs(audio)):.3f}")
    print(f"Выход: {output_path}  RMS {rms_db(out):.1f} dBFS  peak {np.max(np.abs(out)):.3f}")
    print(f"Пресет: {preset_name}, обход: {bypass}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Офлайн-обработка WAV цепочкой Тишины")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--preset", default="Stream")
    parser.add_argument("--bypass", action="store_true")
    args = parser.parse_args()

    process(args.input, args.output, args.preset, args.bypass)


if __name__ == "__main__":
    main()
