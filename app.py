# -*- coding: utf-8 -*-
"""Точка входа Тишина Lite."""

from __future__ import annotations

import argparse
import multiprocessing
import sys
import tempfile
from pathlib import Path


def self_test() -> int:
    """Проверка цепочки и DLL без открытия окна и без аудиоустройств."""
    import numpy as np

    from tishina.audio.chain import Chain
    from tishina.presets import load_preset

    lines: list[str] = []
    ok = True
    try:
        import sounddevice as sd

        lines.append(f"sounddevice: {len(sd.query_devices())} devices")
    except Exception as exc:  # noqa: BLE001
        ok = False
        lines.append(f"sounddevice ERROR: {exc}")

    try:
        from tishina.ui.main_window import MainWindow  # noqa: F401

        lines.append("PySide6 UI import: OK")
    except Exception as exc:  # noqa: BLE001
        ok = False
        lines.append(f"PySide6 ERROR: {exc}")

    try:
        chain = Chain()
        chain.apply_preset(load_preset("Stream"))
        frame = (0.1 * np.sin(2.0 * np.pi * 220.0 * np.arange(480) / 48_000.0)).astype(np.float32)
        output = frame
        for _ in range(20):
            output = chain.process(output)
        finite = bool(np.isfinite(output).all())
        lines.append(
            f"RNNoise: {'OK' if chain.denoise.available else 'MISSING'} "
            f"({chain.denoise.last_error or 'loaded'})"
        )
        lines.append(f"DSP: {'OK' if finite else 'NON-FINITE'}, peak={float(np.max(np.abs(output))):.4f}")
        ok = ok and finite and chain.denoise.available
    except Exception as exc:  # noqa: BLE001
        ok = False
        lines.append(f"DSP ERROR: {exc}")

    text = "\n".join(lines)
    print(text)
    try:
        path = Path(tempfile.gettempdir()) / "tishina_selftest.txt"
        path.write_text(text, encoding="utf-8")
        print(f"Self-test log: {path}")
    except Exception:
        pass
    return 0 if ok else 1


def list_devices() -> None:
    from tishina.audio.engine import AudioEngine

    if not AudioEngine.available():
        print("sounddevice не установлен:", AudioEngine.import_error())
        return

    print("Устройства ввода:")
    for device in AudioEngine.input_devices():
        mark = "  <-- по умолчанию" if device["index"] == AudioEngine.default_input() else ""
        print(
            f'  [{device["index"]:>2}] {device["name"]} | {device["hostapi"]}'
            f' | in={device["max_input_channels"]} | {device["default_samplerate"]:.0f} Hz{mark}'
        )

    print("\nУстройства вывода:")
    cable = AudioEngine.find_cable_output()
    for device in AudioEngine.output_devices():
        mark = "  <-- CABLE Input" if device["index"] == cable else ""
        print(
            f'  [{device["index"]:>2}] {device["name"]} | {device["hostapi"]}'
            f' | out={device["max_output_channels"]} | {device["default_samplerate"]:.0f} Hz{mark}'
        )

    if cable is None:
        print("\nVB-Cable не найден. Установите его с https://vb-audio.com/Cable/")
    else:
        print(f"\nCABLE Input найден: индекс {cable}. В OBS/Discord выбирайте микрофон CABLE Output.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Тишина Lite — микрофонная обработка для Windows")
    parser.add_argument("--list-devices", action="store_true", help="Показать аудиоустройства и выйти")
    parser.add_argument("--self-test", action="store_true", help="Проверить DLL и DSP и выйти")
    parser.add_argument("--version", action="store_true", help="Показать версию и выйти")
    args, _ = parser.parse_known_args()

    if args.self_test:
        raise SystemExit(self_test())

    if args.version:
        from tishina.config import APP_NAME, APP_VERSION

        print(f"{APP_NAME} {APP_VERSION}")
        return

    if args.list_devices:
        list_devices()
        return

    from tishina.ui.main_window import run

    run()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
