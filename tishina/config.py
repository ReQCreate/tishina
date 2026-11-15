# -*- coding: utf-8 -*-
"""Общие настройки и пути."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Tishina Lite"
APP_VERSION = "0.1.0"

SAMPLE_RATE = 48_000
BLOCK_SIZE = 480          # 10 мс при 48 кГц — кадр RNNoise
CHANNELS = 1

# В PyInstaller onedir __file__ уже указывает внутрь _internal/tishina,
# поэтому путь работает и в исходниках, и в собранном приложении.
PACKAGE_DIR = Path(__file__).resolve().parent
PRESETS_DIR = PACKAGE_DIR / "presets"
VENDOR_DIR = PACKAGE_DIR / "vendor"
RNNOISE_DLL = VENDOR_DIR / "rnnoise.dll"


def user_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / "Tishina"
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_presets_dir() -> Path:
    path = user_data_dir() / "presets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(user_data_dir())
    path = Path(base) / "Tishina" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
