# -*- coding: utf-8 -*-
"""Главное окно Тишина Lite."""

from __future__ import annotations

import sys

from PySide6.QtCore import QSettings, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..audio.engine import AudioEngine
from ..config import APP_NAME, APP_VERSION
from ..presets import list_presets
from .guide import SetupGuideDialog
from .meters import LevelMeter


STYLE = """
QWidget {
    background: #0f1115;
    color: #e6e8ee;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QMainWindow { background: #0f1115; }
QLabel#title {
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 4px;
    color: #ffffff;
}
QLabel#subtitle { color: #7f879b; font-size: 12px; }
QLabel#pill {
    background: #1b202b;
    border: 1px solid #2a3140;
    border-radius: 12px;
    padding: 5px 12px;
    color: #98a1b5;
    font-weight: 600;
}
QLabel#pill[running="true"] {
    background: #103525;
    border-color: #1e6b48;
    color: #5ee2a0;
}
QLabel#metric { color: #9aa3b7; }
QLabel#warning { color: #ffb86b; }
QLabel#error { color: #ff7b7b; }
QGroupBox {
    border: 1px solid #232936;
    border-radius: 12px;
    margin-top: 12px;
    padding: 14px 12px 12px 12px;
    background: #12151c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #8b93a7;
    font-weight: 600;
}
QComboBox, QPushButton {
    background: #171b23;
    border: 1px solid #2a3040;
    border-radius: 8px;
    padding: 7px 11px;
    min-height: 18px;
}
QComboBox:hover, QPushButton:hover { border-color: #4f7cff; }
QComboBox:disabled, QPushButton:disabled { color: #5e6678; border-color: #222835; }
QComboBox QAbstractItemView {
    background: #171b23;
    border: 1px solid #2a3040;
    selection-background-color: #24418c;
}
QPushButton#primary {
    background: #2f6bff;
    border: none;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#primary:hover { background: #4a7fff; }
QPushButton#primary:disabled { background: #23345e; color: #8290ad; }
QPushButton#danger { color: #ff8a8a; }
QToolButton#help {
    background: #171b23;
    border: 1px solid #2a3040;
    border-radius: 17px;
}
QToolButton#help:hover {
    background: #1b2130;
    border-color: #4f7cff;
}
QCheckBox { spacing: 8px; color: #c5cbda; }
QSlider::groove:horizontal {
    height: 6px;
    background: #222836;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #2f6bff;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
    background: #dfe7ff;
}
QSlider::handle:horizontal:hover { background: #ffffff; }
QStatusBar { color: #7f879b; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.engine = AudioEngine()
        self.settings = QSettings("Tishina", "TishinaLite")
        self.tray: QSystemTrayIcon | None = None
        self.tray_menu: QMenu | None = None
        self.tray_mute: QAction | None = None
        self.tray_bypass: QAction | None = None
        self._tray_hint_shown = False
        self._syncing = False
        self._sliders: dict[str, QSlider] = {}
        self._value_labels: dict[str, QLabel] = {}
        self._suffixes = {
            "denoise": "%",
            "gate": " dB",
            "presence": " dB",
            "compression": "%",
            "output": " dB",
        }

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(900, 660)
        self.resize(980, 720)
        self.setStyleSheet(STYLE)

        self._build_ui()
        self._create_tray()
        self._create_shortcuts()
        self._restore_settings()
        self._refresh_devices()
        self._apply_initial_preset()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_ui)
        self.timer.start(50)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(0)
        title = QLabel("ТИШИНА")
        title.setObjectName("title")
        subtitle = QLabel("микрофон · шумодав · виртуальный кабель")
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch(1)
        self.help_btn = QToolButton()
        self.help_btn.setObjectName("help")
        self.help_btn.setIcon(self._make_help_icon())
        self.help_btn.setIconSize(QSize(22, 22))
        self.help_btn.setFixedSize(34, 34)
        self.help_btn.setToolTip("Инструкция: как установить VB-Cable и настроить программу")
        self.help_btn.setAccessibleName("Инструкция по настройке")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.clicked.connect(self._show_guide)
        header.addWidget(self.help_btn)
        header.addSpacing(8)
        self.status_pill = QLabel("ОСТАНОВЛЕН")
        self.status_pill.setObjectName("pill")
        self.status_pill.setProperty("running", "false")
        header.addWidget(self.status_pill)
        root.addLayout(header)

        root.addWidget(self._build_devices_group())
        root.addWidget(self._build_meters_group())
        root.addWidget(self._build_processing_group(), 1)

        footer = QHBoxLayout()
        self.detail_label = QLabel("Готово к запуску")
        self.detail_label.setObjectName("metric")
        self.detail_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        footer.addWidget(self.detail_label, 1)
        footer.addWidget(self.error_label)
        root.addLayout(footer)

    def _build_devices_group(self) -> QGroupBox:
        group = QGroupBox("Устройства")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Микрофон"), 0, 0)
        self.input_combo = QComboBox()
        self.input_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.input_combo, 0, 1)

        grid.addWidget(QLabel("Выход"), 1, 0)
        self.output_combo = QComboBox()
        self.output_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.output_combo, 1, 1)

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self._refresh_devices)
        grid.addWidget(self.refresh_btn, 0, 2)

        self.start_btn = QPushButton("Старт")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumWidth(140)
        self.start_btn.clicked.connect(self._toggle_start)
        grid.addWidget(self.start_btn, 1, 2)

        self.cable_warning = QLabel("")
        self.cable_warning.setObjectName("warning")
        self.cable_warning.setWordWrap(True)
        grid.addWidget(self.cable_warning, 2, 0, 1, 2)

        self.cable_link = QPushButton("Скачать VB-Cable")
        self.cable_link.setObjectName("danger")
        self.cable_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://vb-audio.com/Cable/")))
        grid.addWidget(self.cable_link, 2, 2)

        self.denoise_warning = QLabel("")
        self.denoise_warning.setObjectName("warning")
        self.denoise_warning.setWordWrap(True)
        self.denoise_warning.hide()
        grid.addWidget(self.denoise_warning, 3, 0, 1, 3)

        grid.setColumnStretch(1, 1)
        return group

    def _build_meters_group(self) -> QGroupBox:
        group = QGroupBox("Уровни и телеметрия")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.input_meter = LevelMeter("Вход")
        self.output_meter = LevelMeter("Выход")
        layout.addWidget(self.input_meter)
        layout.addWidget(self.output_meter)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(24)
        metrics.setVerticalSpacing(4)
        self.lbl_noise = QLabel("Шум: —")
        self.lbl_vad = QLabel("Голос: —")
        self.lbl_lufs = QLabel("Громкость: —")
        self.lbl_latency = QLabel("Задержка: —")
        self.lbl_cpu = QLabel("CPU: —")
        self.lbl_underruns = QLabel("Срывы: —")
        labels = (
            (self.lbl_noise, 0, 0),
            (self.lbl_vad, 0, 1),
            (self.lbl_lufs, 0, 2),
            (self.lbl_latency, 1, 0),
            (self.lbl_cpu, 1, 1),
            (self.lbl_underruns, 1, 2),
        )
        for label, row, column in labels:
            label.setObjectName("metric")
            metrics.addWidget(label, row, column)
        for column in range(3):
            metrics.setColumnStretch(column, 1)
        layout.addLayout(metrics)
        return group

    def _build_processing_group(self) -> QGroupBox:
        group = QGroupBox("Обработка")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Пресет"), 0, 0)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([name[:1].upper() + name[1:] for name in list_presets()])
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        grid.addWidget(self.preset_combo, 0, 1)

        self.bypass_check = QCheckBox("Обход")
        self.bypass_check.toggled.connect(self._set_bypass)
        grid.addWidget(self.bypass_check, 0, 2)

        self.mute_btn = QPushButton("Mute")
        self.mute_btn.setCheckable(True)
        self.mute_btn.toggled.connect(self._set_mute)
        grid.addWidget(self.mute_btn, 0, 3)

        self._add_slider(grid, 1, "denoise", "Шумодав", 0, 100, 75)
        self._add_slider(grid, 2, "gate", "Гейт", -70, -20, -42)
        self._add_slider(grid, 3, "presence", "Присутствие", -6, 6, 2)
        self._add_slider(grid, 4, "compression", "Компрессия", 0, 100, 50)
        self._add_slider(grid, 5, "output", "Выход", -12, 12, 0)

        hint = QLabel("Совет: начните с пресета Stream, затем подстройте гейт под свой микрофон.")
        hint.setObjectName("metric")
        hint.setWordWrap(True)
        grid.addWidget(hint, 6, 0, 1, 4)

        grid.setColumnStretch(1, 1)
        return group

    def _add_slider(
        self,
        grid: QGridLayout,
        row: int,
        key: str,
        title: str,
        minimum: int,
        maximum: int,
        value: int,
    ) -> None:
        label = QLabel(title)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        slider.valueChanged.connect(lambda v, k=key: self._on_slider(k, v))
        value_label = QLabel(f"{value}{self._suffixes[key]}")
        value_label.setMinimumWidth(62)
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        grid.addWidget(label, row, 0)
        grid.addWidget(slider, row, 1)
        grid.addWidget(value_label, row, 2)

        self._sliders[key] = slider
        self._value_labels[key] = value_label

    # ------------------------------------------------------------------
    # Tray / hotkeys
    # ------------------------------------------------------------------
    def _create_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = self._make_icon()
        QApplication.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(f"{APP_NAME} {APP_VERSION}")

        menu = QMenu()
        self.tray_menu = menu
        show_action = menu.addAction("Показать")
        show_action.triggered.connect(self._show_window)
        guide_action = menu.addAction("Инструкция по настройке")
        guide_action.triggered.connect(self._show_guide)
        menu.addSeparator()
        self.tray_mute = menu.addAction("Mute")
        self.tray_mute.setCheckable(True)
        self.tray_mute.toggled.connect(self._set_mute)
        self.tray_bypass = menu.addAction("Обход")
        self.tray_bypass.setCheckable(True)
        self.tray_bypass.toggled.connect(self._set_bypass)
        menu.addSeparator()
        quit_action = menu.addAction("Выход")
        quit_action.triggered.connect(self._quit_app)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason) -> None:  # noqa: ANN001
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_window()

    def _create_shortcuts(self) -> None:
        self._mute_shortcut = QShortcut(QKeySequence("Ctrl+Alt+M"), self)
        self._mute_shortcut.activated.connect(self._toggle_mute)
        self._bypass_shortcut = QShortcut(QKeySequence("Ctrl+Alt+B"), self)
        self._bypass_shortcut.activated.connect(self._toggle_bypass)

    @staticmethod
    def _make_icon() -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2f6bff"))
        painter.drawEllipse(2, 2, 60, 60)
        painter.setPen(QPen(QColor("#ffffff"), 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        points = [(16, 32), (22, 32), (26, 20), (31, 44), (36, 26), (41, 38), (46, 32), (50, 32)]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            painter.drawLine(x1, y1, x2, y2)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _make_help_icon() -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#2a3040"), 2))
        painter.setBrush(QColor("#171b23"))
        painter.drawEllipse(3, 3, 58, 58)
        painter.setPen(QColor("#dfe5f1"))
        painter.setFont(QFont("Segoe UI", 26, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "?")
        painter.end()
        return QIcon(pixmap)

    def _show_guide(self) -> None:
        dialog = SetupGuideDialog(self, STYLE)
        dialog.exec()

    # ------------------------------------------------------------------
    # Settings / devices
    # ------------------------------------------------------------------
    def _restore_settings(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self._saved_input = str(self.settings.value("input_name", "") or "")
        self._saved_output = str(self.settings.value("output_name", "") or "")
        saved_preset = str(self.settings.value("preset", "Stream") or "Stream")
        index = -1
        for i in range(self.preset_combo.count()):
            if self.preset_combo.itemText(i).lower() == saved_preset.lower():
                index = i
                break
        if index < 0:
            index = self.preset_combo.findText("Stream")
        if index >= 0:
            self.preset_combo.setCurrentIndex(index)
        self.bypass_check.setChecked(bool(self.settings.value("bypass", False, type=bool)))
        self.mute_btn.setChecked(bool(self.settings.value("mute", False, type=bool)))

    def _refresh_devices(self) -> None:
        current_input = self._selected_name(self.input_combo)
        current_output = self._selected_name(self.output_combo)
        self.input_combo.clear()
        self.output_combo.clear()

        try:
            inputs = AudioEngine.input_devices()
            outputs = AudioEngine.output_devices()
        except Exception as exc:  # noqa: BLE001
            self.cable_warning.setText(f"Ошибка устройств: {exc}")
            return

        for device in inputs:
            self.input_combo.addItem(AudioEngine.display_name(device), device)
        for device in outputs:
            self.output_combo.addItem(AudioEngine.display_name(device), device)

        self._select_device(self.input_combo, current_input or self._saved_input, AudioEngine.default_input())
        cable = AudioEngine.find_cable_output()
        self._select_device(self.output_combo, current_output or self._saved_output, cable)

        if not inputs:
            self.cable_warning.setText("Микрофоны не найдены. Проверьте настройки Windows.")
        elif cable is None:
            self.cable_warning.setText(
                "VB-Cable не найден. Установите виртуальный кабель, чтобы приложения видели «CABLE Output»."
            )
        else:
            self.cable_warning.setText("VB-Cable найден: приложения должны выбрать микрофон «CABLE Output».")

        self.cable_link.setVisible(cable is None)
        self._update_status_pill(False)
        self._check_denoise()

    @staticmethod
    def _selected_name(combo: QComboBox) -> str:
        data = combo.currentData()
        return str(data["name"]) if data else ""

    @staticmethod
    def _select_device(combo: QComboBox, name: str, fallback_index: int | None) -> None:
        if name:
            for i in range(combo.count()):
                data = combo.itemData(i)
                if data and data["name"] == name:
                    combo.setCurrentIndex(i)
                    return
        if fallback_index is not None:
            for i in range(combo.count()):
                data = combo.itemData(i)
                if data and data["index"] == fallback_index:
                    combo.setCurrentIndex(i)
                    return
        if combo.count():
            combo.setCurrentIndex(0)

    def _apply_initial_preset(self) -> None:
        try:
            self.engine.set_preset(self.preset_combo.currentText() or "Stream")
        except Exception as exc:  # noqa: BLE001
            self.error_label.setText(str(exc))
        self._sync_controls_from_chain()
        self._set_bypass(self.bypass_check.isChecked())
        self._set_mute(self.mute_btn.isChecked())

    # ------------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------------
    def _toggle_start(self) -> None:
        if self.engine.running:
            self.engine.stop()
            self._set_running_ui(False)
            return

        input_data = self.input_combo.currentData()
        output_data = self.output_combo.currentData()
        if not input_data or not output_data:
            QMessageBox.warning(self, "Устройства", "Выберите микрофон и выход CABLE Input.")
            return

        self.start_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.engine.start(int(input_data["index"]), int(output_data["index"]))
            self._set_running_ui(True)
            self._save_settings()
        except Exception as exc:  # noqa: BLE001
            self.engine.stop()
            self._set_running_ui(False)
            QMessageBox.critical(self, "Не удалось запустить", str(exc))
        finally:
            QApplication.restoreOverrideCursor()
            self.start_btn.setEnabled(True)

    def _set_running_ui(self, running: bool) -> None:
        self.start_btn.setText("Стоп" if running else "Старт")
        self.start_btn.setObjectName("danger" if running else "primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.input_combo.setEnabled(not running)
        self.output_combo.setEnabled(not running)
        self.refresh_btn.setEnabled(not running)
        self._update_status_pill(running)

    def _update_status_pill(self, running: bool) -> None:
        text = "РАБОТАЕТ" if running else "ОСТАНОВЛЕН"
        prop = "true" if running else "false"
        if self.status_pill.text() == text and self.status_pill.property("running") == prop:
            return
        self.status_pill.setText(text)
        self.status_pill.setProperty("running", prop)
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------
    def _on_preset_changed(self, name: str) -> None:
        if not name or self._syncing:
            return
        try:
            self.engine.set_preset(name)
        except Exception as exc:  # noqa: BLE001
            self.error_label.setText(str(exc))
            return
        self._sync_controls_from_chain()
        self.settings.setValue("preset", name)

    def _sync_controls_from_chain(self) -> None:
        chain = self.engine.chain
        self._syncing = True
        try:
            self._set_slider("denoise", int(round(chain.denoise.mix * 100)))
            self._set_slider("gate", int(round(chain.gate.threshold_db)))
            self._set_slider("presence", int(round(chain.eq.presence_gain)))
            amount = int(round((max(1.0, chain.compressor.ratio) - 1.0) / 0.03))
            self._set_slider("compression", max(0, min(100, amount)))
            self._set_slider("output", int(round(chain.gain.gain_db)))
            self.bypass_check.setChecked(chain.bypass)
            self.mute_btn.setChecked(chain.gain.mute)
        finally:
            self._syncing = False

    def _set_slider(self, key: str, value: int) -> None:
        slider = self._sliders.get(key)
        if slider is None:
            return
        slider.blockSignals(True)
        slider.setValue(value)
        slider.blockSignals(False)
        self._update_value_label(key, slider.value())

    def _update_value_label(self, key: str, value: int) -> None:
        label = self._value_labels.get(key)
        if label is not None:
            label.setText(f"{value}{self._suffixes.get(key, '')}")

    def _on_slider(self, key: str, value: int) -> None:
        self._update_value_label(key, value)
        if self._syncing:
            return

        chain = self.engine.chain
        if key == "denoise":
            self.engine.set_module_param("denoise", "mix", value / 100.0)
        elif key == "gate":
            self.engine.set_module_param("gate", "threshold_db", float(value))
        elif key == "presence":
            self.engine.set_module_param("eq", "presence_gain", float(value))
        elif key == "compression":
            amount = float(value)
            chain.compressor.set_params(
                threshold_db=-30.0 + 0.20 * amount,
                ratio=1.0 + 0.03 * amount,
                makeup_db=0.04 * amount,
            )
        elif key == "output":
            self.engine.set_module_param("gain", "gain_db", float(value))

    def _set_bypass(self, checked: bool) -> None:
        self.engine.set_bypass(bool(checked))
        if self.bypass_check.isChecked() != bool(checked):
            self.bypass_check.blockSignals(True)
            self.bypass_check.setChecked(bool(checked))
            self.bypass_check.blockSignals(False)
        if self.tray_bypass is not None and self.tray_bypass.isChecked() != bool(checked):
            self.tray_bypass.blockSignals(True)
            self.tray_bypass.setChecked(bool(checked))
            self.tray_bypass.blockSignals(False)
        self.settings.setValue("bypass", bool(checked))

    def _set_mute(self, checked: bool) -> None:
        self.engine.set_mute(bool(checked))
        if self.mute_btn.isChecked() != bool(checked):
            self.mute_btn.blockSignals(True)
            self.mute_btn.setChecked(bool(checked))
            self.mute_btn.blockSignals(False)
        self.mute_btn.setText("Muted" if checked else "Mute")
        if self.tray_mute is not None and self.tray_mute.isChecked() != bool(checked):
            self.tray_mute.blockSignals(True)
            self.tray_mute.setChecked(bool(checked))
            self.tray_mute.blockSignals(False)
        self.settings.setValue("mute", bool(checked))

    def _toggle_mute(self) -> None:
        self._set_mute(not self.mute_btn.isChecked())

    def _toggle_bypass(self) -> None:
        self._set_bypass(not self.bypass_check.isChecked())

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------
    def _update_ui(self) -> None:
        status = self.engine.status()
        self.input_meter.set_level(status["input_peak_db"], status["input_rms_db"])
        self.output_meter.set_level(status["output_peak_db"], status["output_rms_db"])

        self.lbl_noise.setText(f"Шум: {status['noise_floor_db']:.1f} dB")
        vad = float(status["vad"])
        self.lbl_vad.setText(f"Голос: {'да' if vad >= 0.4 else 'нет'} ({vad * 100:.0f}%)")
        lufs = float(status["lufs"])
        self.lbl_lufs.setText("Громкость: —" if lufs < -60.0 else f"Громкость: {lufs:.1f} LUFS")
        self.lbl_latency.setText(f"Задержка: {status['latency_ms']:.0f} мс")
        self.lbl_cpu.setText(f"CPU: {status['cpu_percent']:.1f}%")
        self.lbl_underruns.setText(f"Срывы: {status['underruns']}")

        if status["last_error"]:
            self.error_label.setText(str(status["last_error"])[:120])
        else:
            self.error_label.setText("")

        if status["running"]:
            route = f"{status['input_name'] or '—'} → {status['output_name'] or '—'}"
        else:
            route = f"{self._selected_name(self.input_combo) or '—'} → {self._selected_name(self.output_combo) or '—'}"
        self.detail_label.setText(f"Пресет: {self.preset_combo.currentText()}   ·   {route}")
        self._update_status_pill(bool(status["running"]))
        self._check_denoise()

    def _check_denoise(self) -> None:
        denoise = self.engine.chain.denoise
        if denoise.available:
            if self.denoise_warning.isVisible():
                self.denoise_warning.hide()
        else:
            text = f"RNNoise недоступен: {denoise.last_error}. Работает только обычный DSP."
            if self.denoise_warning.text() != text:
                self.denoise_warning.setText(text)
            if not self.denoise_warning.isVisible():
                self.denoise_warning.show()

    # ------------------------------------------------------------------
    # Window / tray lifecycle
    # ------------------------------------------------------------------
    def _save_settings(self) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("input_name", self._selected_name(self.input_combo))
        self.settings.setValue("output_name", self._selected_name(self.output_combo))
        self.settings.setValue("preset", self.preset_combo.currentText())
        self.settings.setValue("mute", self.mute_btn.isChecked())
        self.settings.setValue("bypass", self.bypass_check.isChecked())

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self) -> None:
        self._save_settings()
        self.engine.stop()
        if self.tray is not None:
            self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:  # noqa: ANN001
        self._save_settings()
        if self.tray is not None and self.tray.isVisible():
            event.ignore()
            self.hide()
            if not self._tray_hint_shown:
                self.tray.showMessage(
                    APP_NAME,
                    "Приложение свернуто в трей. В окне: Ctrl+Alt+M — mute, Ctrl+Alt+B — обход.",
                    QSystemTrayIcon.Information,
                    3000,
                )
                self._tray_hint_shown = True
        else:
            self.engine.stop()
            event.accept()


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Tishina")
    app.setStyle("Fusion")
    window = MainWindow()
    app.setQuitOnLastWindowClosed(window.tray is None)
    window.show()
    sys.exit(app.exec())
