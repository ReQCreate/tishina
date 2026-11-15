# -*- coding: utf-8 -*-
"""Генерация app.ico для окна и exe."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen

ROOT = Path(__file__).resolve().parents[1]


def make_icon(path: Path) -> None:
    size = 256
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#0f1115"))
    painter.drawRoundedRect(0, 0, size, size, 56, 56)
    painter.setBrush(QColor("#2f6bff"))
    painter.drawEllipse(18, 18, size - 36, size - 36)

    painter.setPen(QPen(QColor("#ffffff"), 16, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    raw = [(64, 128), (88, 128), (104, 78), (124, 178), (144, 104), (164, 152), (184, 128), (200, 128)]
    points = [(x * size // 256, y * size // 256) for x, y in raw]
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        painter.drawLine(x1, y1, x2, y2)
    painter.end()

    if not image.save(str(path), "ICO"):
        raise RuntimeError(f"Не удалось сохранить {path}")
    print(f"Готово: {path}")


if __name__ == "__main__":
    make_icon(ROOT / "app.ico")
