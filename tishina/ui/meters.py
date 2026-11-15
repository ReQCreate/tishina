# -*- coding: utf-8 -*-
"""Простые индикаторы уровня."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget


class LevelMeter(QWidget):
    """Горизонтальный индикатор пика/среднего уровня в дБ."""

    def __init__(self, label: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = label
        self._db = -90.0
        self._peak = -90.0
        self.setMinimumHeight(32)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def sizeHint(self) -> QSize:
        return QSize(420, 32)

    def set_level(self, db: float, peak: float | None = None) -> None:
        self._db = max(-90.0, min(0.0, float(db)))
        if peak is not None:
            self._peak = max(-90.0, min(0.0, float(peak)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        height = self.height()
        width = self.width()

        label_rect = QRect(0, 0, 74, height)
        painter.setPen(QColor("#8b93a7"))
        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, self._label)

        bar = QRect(80, 7, max(10, width - 84), max(10, height - 14))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1a1f2a"))
        painter.drawRoundedRect(bar, 4, 4)

        fraction = max(0.0, min(1.0, (self._db + 60.0) / 60.0))
        if fraction > 0.0:
            fill_width = int(bar.width() * fraction)
            fill = QRect(bar.left(), bar.top(), max(2, fill_width), bar.height())
            gradient = QLinearGradient(bar.left(), 0, bar.right(), 0)
            gradient.setColorAt(0.0, QColor("#27d17f"))
            gradient.setColorAt(0.65, QColor("#f4d03f"))
            gradient.setColorAt(1.0, QColor("#ff5c5c"))
            painter.setBrush(gradient)
            painter.drawRoundedRect(fill, 4, 4)

        if self._peak > -60.0:
            x = bar.left() + int(bar.width() * ((self._peak + 60.0) / 60.0))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(x, bar.top(), x, bar.bottom())

        painter.setPen(QColor("#dfe5f1"))
        painter.drawText(bar.adjusted(0, 0, -8, 0), Qt.AlignRight | Qt.AlignVCenter, f"{self._db:.1f} dB")
        painter.end()
