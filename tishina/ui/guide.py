# -*- coding: utf-8 -*-
"""Встроенная инструкция по настройке «Тишины» и VB-Cable."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

VB_CABLE_URL = "https://vb-audio.com/Cable/"

GUIDE_HTML = """
<html>
<head>
<style>
body {
    color: #dfe5f1;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    line-height: 1.55;
    margin: 4px;
}
h2 {
    color: #ffffff;
    font-size: 16px;
    margin-top: 18px;
    margin-bottom: 6px;
}
h2:first-child { margin-top: 0; }
p { margin: 6px 0; }
ul, ol { margin: 6px 0 6px 18px; }
li { margin: 4px 0; }
b { color: #ffffff; }
a { color: #7aa2ff; text-decoration: none; }
code {
    color: #9fd0ff;
    background: #1a1f2a;
    font-family: "Consolas", monospace;
    padding: 1px 4px;
}
.note {
    background: #151a23;
    border-left: 3px solid #f0b35a;
    padding: 9px 12px;
    margin: 10px 0;
}
.good {
    background: #10231a;
    border-left: 3px solid #3bc47a;
    padding: 9px 12px;
    margin: 10px 0;
}
.bad {
    background: #241417;
    border-left: 3px solid #ff6b6b;
    padding: 9px 12px;
    margin: 10px 0;
}
.small { color: #8b93a7; font-size: 12px; }
</style>
</head>
<body>

<h2>1. Установите VB-Cable</h2>
<p>VB-Cable — отдельный виртуальный аудиокабель. Он не входит в «Тишину» и ставится один раз.</p>
<ol>
    <li>Откройте официальный сайт: <a href="https://vb-audio.com/Cable/">vb-audio.com/Cable</a>. Кнопка «Скачать VB-Cable» в приложении ведёт туда же.</li>
    <li>Скачайте пакет <code>VBCABLE_Driver_Pack...</code>.</li>
    <li>Распакуйте архив.</li>
    <li>Запустите <code>VBCable_Setup_x64.exe</code> <b>от имени администратора</b>.</li>
    <li>Установите драйвер и <b>перезагрузите компьютер</b>, если установщик попросит.</li>
</ol>
<div class="note">
    <b>Важно:</b> для обычной работы нужен именно <b>VB-CABLE</b>. Версии A+B и C+D — это отдельные дополнительные пакеты, они не нужны.
</div>
<p class="small">Если <code>CABLE Input</code> уже есть в списке устройств, установка не нужна — переходите к пункту 2.</p>

<h2>2. Настройте «Тишину»</h2>
<ol>
    <li>Вернитесь в «Тишину» и нажмите <b>«Обновить»</b>.</li>
    <li><b>Микрофон</b> — выберите свой физический микрофон. Лучше вариант с <code>WASAPI</code> и <code>48000 Hz</code>.</li>
    <li><b>Выход</b> — выберите <code>CABLE Input (VB-Audio Virtual Cable)</code>.</li>
    <li>Выберите пресет <b>Stream</b> или <b>Chat</b>.</li>
    <li>Нажмите <b>«Старт»</b>. Статус должен стать <b>РАБОТАЕТ</b>.</li>
    <li>Скажите что-нибудь — индикаторы «Вход» и «Выход» должны двигаться.</li>
</ol>
<div class="good">
    <b>Правильный маршрут:</b> «Тишина» пишет в <code>CABLE Input</code>, а OBS/Discord/Zoom читают из <code>CABLE Output</code>.
</div>

<h2>3. OBS</h2>
<ol>
    <li>Добавьте источник <b>Audio Input Capture</b>.</li>
    <li>Выберите устройство <code>CABLE Output (VB-Audio Virtual Cable)</code>.</li>
    <li>В настройках OBS → Аудио поставьте частоту <code>48 kHz</code>.</li>
    <li>Уберите или замьютьте прямой микрофон, если он добавлен вторым источником.</li>
</ol>

<h2>4. Discord</h2>
<p>Настройки → Голос и видео:</p>
<ul>
    <li><b>Устройство ввода:</b> <code>CABLE Output (VB-Audio Virtual Cable)</code>.</li>
    <li><b>Шумоподавление:</b> выключить.</li>
    <li><b>Эхоподавление:</b> выключить.</li>
    <li><b>Автоматическая регулировка усиления:</b> выключить.</li>
</ul>
<p class="small">Иначе Discord будет повторно обрабатывать уже обработанный звук.</p>

<h2>5. Zoom, Telegram, браузер и игры</h2>
<p>Везде выбирайте микрофон <code>CABLE Output (VB-Audio Virtual Cable)</code>. Настройки микрофона внутри приложения лучше отключить, если они дублируют шумодав.</p>

<h2>6. Трей и горячие клавиши</h2>
<ul>
    <li>Закрытие окна сворачивает «Тишину» в трей — обработка продолжается.</li>
    <li>Выход — через меню иконки в трее.</li>
    <li><code>Ctrl+Alt+M</code> — Mute.</li>
    <li><code>Ctrl+Alt+B</code> — обход обработки.</li>
</ul>

<h2>7. Если что-то не работает</h2>
<div class="bad">
    <b>Нет CABLE Input в списке.</b> Нажмите «Обновить», проверьте установку VB-Cable и перезагрузите компьютер.
</div>
<div class="bad">
    <b>Индикатор «Вход» не двигается.</b> Проверьте, что выбран нужный микрофон, он не замьючен и Windows разрешает доступ к микрофону. Закройте программы, которые монопольно заняли микрофон.
</div>
<div class="bad">
    <b>В OBS/Discord тишина.</b> В «Тишине» выход должен быть <code>CABLE Input</code>, а в приложении микрофон — <code>CABLE Output</code>. Не наоборот.
</div>
<div class="bad">
    <b>Слышно эхо.</b> Уберите прямой микрофон из OBS/Discord и отключите встроенные шумодавы приложения.
</div>
<div class="bad">
    <b>Гейт обрезает слова.</b> Опустите порог гейта до <code>-48…-50 dB</code>. Если пролезает шум — поднимите до <code>-36…-38 dB</code>.
</div>

<p class="small">Сайт VB-Cable: <a href="https://vb-audio.com/Cable/">https://vb-audio.com/Cable/</a>. VB-Cable — donationware от VB-Audio.</p>

</body>
</html>
"""

DIALOG_STYLE = """
QDialog { background: #0f1115; }
QLabel#guideTitle { font-size: 22px; font-weight: 700; color: #ffffff; }
QLabel#guideSubtitle { color: #7f879b; font-size: 12px; }
QTextBrowser {
    background: #0f1115;
    border: 1px solid #232936;
    border-radius: 10px;
    padding: 8px;
}
QTextBrowser QScrollBar:vertical {
    background: #12151c;
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}
QTextBrowser QScrollBar::handle:vertical {
    background: #2a3040;
    border-radius: 5px;
    min-height: 30px;
}
QTextBrowser QScrollBar::handle:vertical:hover { background: #4f7cff; }
QTextBrowser QScrollBar::add-line:vertical,
QTextBrowser QScrollBar::sub-line:vertical {
    height: 0;
}
QTextBrowser QScrollBar::add-page:vertical,
QTextBrowser QScrollBar::sub-page:vertical {
    background: none;
}
QPushButton#primary {
    background: #2f6bff;
    border: none;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#primary:hover { background: #4a7fff; }
"""


class SetupGuideDialog(QDialog):
    """Модальное окно с пошаговой инструкцией."""

    def __init__(self, parent: QWidget | None = None, stylesheet: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Инструкция по настройке")
        self.setMinimumSize(760, 600)
        self.resize(820, 680)
        self.setStyleSheet((stylesheet or "") + DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        title = QLabel("Как настроить «Тишину»")
        title.setObjectName("guideTitle")
        subtitle = QLabel("VB-Cable + маршрутизация звука в OBS, Discord и других приложениях")
        subtitle.setObjectName("guideSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(GUIDE_HTML)
        layout.addWidget(self.browser, 1)

        buttons = QHBoxLayout()
        open_button = QPushButton("Открыть сайт VB-Cable")
        open_button.setObjectName("primary")
        open_button.setMinimumWidth(190)
        open_button.clicked.connect(self._open_vb_cable)
        close_button = QPushButton("Закрыть")
        close_button.setMinimumWidth(110)
        close_button.clicked.connect(self.accept)
        buttons.addWidget(open_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    @staticmethod
    def _open_vb_cable() -> None:
        QDesktopServices.openUrl(QUrl(VB_CABLE_URL))
