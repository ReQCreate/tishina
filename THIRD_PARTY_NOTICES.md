# Сторонние компоненты и лицензии

«Тишина Lite» использует сторонние библиотеки и бинарные компоненты. Ниже перечислены основные из них. Полные тексты лицензий лежат в папке [`licenses/`](licenses/).

## Основной код

Код «Тишины» распространяется по лицензии **MIT**. См. [`LICENSE`](LICENSE).

## Аудио и DSP

| Компонент | Лицензия | Где используется |
|---|---|---|
| RNNoise | BSD-3-Clause | `tishina/vendor/rnnoise.dll`, шумодав |
| pyrnnoise (Windows-сборка DLL) | Apache-2.0 | происхождение `rnnoise.dll` |
| NumPy | BSD-3-Clause | обработка массивов |
| SciPy | BSD-3-Clause | фильтры и DSP |
| sounddevice / PortAudio | MIT | ввод-вывод звука |

Тексты: [`licenses/rnnoise.txt`](licenses/rnnoise.txt), [`licenses/pyrnnoise.txt`](licenses/pyrnnoise.txt), [`licenses/numpy.txt`](licenses/numpy.txt), [`licenses/scipy.txt`](licenses/scipy.txt), [`licenses/sounddevice.txt`](licenses/sounddevice.txt).

## Интерфейс и упаковка

| Компонент | Лицензия | Примечание |
|---|---|---|
| PySide6 / Qt for Python | LGPL-3.0 | Qt-библиотеки поставляются отдельными файлами в onedir-сборке |
| shiboken6 | LGPL-3.0 | привязки Qt |
| PyInstaller | GPL-2.0 с исключением для загрузчика | используется для сборки `.exe` |

Тексты: [`licenses/LGPL-3.0.txt`](licenses/LGPL-3.0.txt), [`licenses/GPL-3.0.txt`](licenses/GPL-3.0.txt), [`licenses/pyinstaller.txt`](licenses/pyinstaller.txt).

## VB-Cable

VB-Cable — отдельный продукт VB-Audio. Он **не входит** в установщик и не распространяется вместе с «Тишиной». Ссылка на официальный сайт: <https://vb-audio.com/Cable/>.

Пользователь устанавливает VB-Cable самостоятельно на условиях VB-Audio.

## Установщик

Установщик собран с помощью Inno Setup. Сам Inno Setup не входит в состав распространяемого установщика.
