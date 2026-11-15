# -*- coding: utf-8 -*-
"""Загрузка и сохранение пресетов."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import PRESETS_DIR, user_presets_dir


def _preset_dirs() -> list[Path]:
    return [PRESETS_DIR, user_presets_dir()]


def list_presets() -> list[str]:
    names: set[str] = set()
    for directory in _preset_dirs():
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            names.add(path.stem)
    return sorted(names, key=str.lower)


def preset_path(name: str) -> Path | None:
    for directory in _preset_dirs():
        path = directory / f"{name}.json"
        if path.exists():
            return path
    # Windows регистронезависим, но запасной поиск полезен и для тестов.
    lowered = name.lower()
    for directory in _preset_dirs():
        if not directory.exists():
            continue
        for path in directory.glob("*.json"):
            if path.stem.lower() == lowered:
                return path
    return None


def load_preset(name: str) -> dict[str, Any]:
    path = preset_path(name)
    if path is None:
        raise FileNotFoundError(f"Пресет не найден: {name}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_preset(name: str, data: dict[str, Any]) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in " _-").strip()
    if not safe:
        raise ValueError("Пустое имя пресета")
    path = user_presets_dir() / f"{safe}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    return path
