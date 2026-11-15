# -*- coding: utf-8 -*-
"""Печать аудиоустройств Windows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tishina.audio.engine import AudioEngine  # noqa: E402


def main() -> None:
    if not AudioEngine.available():
        print("sounddevice не установлен:", AudioEngine.import_error())
        return

    print("Все устройства:")
    for device in AudioEngine.list_devices():
        print(
            f'[{device["index"]:>2}] {device["name"]}\n'
            f'     hostapi={device["hostapi"]}  in={device["max_input_channels"]}  '
            f'out={device["max_output_channels"]}  sr={device["default_samplerate"]:.0f}'
        )

    default_input = AudioEngine.default_input()
    cable = AudioEngine.find_cable_output()
    print("\nПо умолчанию микрофон:", default_input)
    print("CABLE Input:", cable)
    if cable is None:
        print("VB-Cable не найден: https://vb-audio.com/Cable/")


if __name__ == "__main__":
    main()
