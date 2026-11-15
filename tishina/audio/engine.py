# -*- coding: utf-8 -*-
"""Аудио-движок: микрофон -> обработка -> виртуальный кабель."""

from __future__ import annotations

import queue
import threading
import time
from typing import Any

import numpy as np

try:
    import sounddevice as sd
except Exception as exc:  # noqa: BLE001
    sd = None
    _SD_IMPORT_ERROR = str(exc)
else:
    _SD_IMPORT_ERROR = ""

from ..config import BLOCK_SIZE, SAMPLE_RATE
from .analysis import AudioAnalyzer
from .chain import Chain
from ..presets import load_preset


class AudioEngine:
    """Захват микрофона, обработка и вывод в CABLE Input."""

    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sample_rate = sample_rate
        self.blocksize = BLOCK_SIZE
        self.chain = Chain(sample_rate=sample_rate)
        self.analyzer = AudioAnalyzer(sample_rate=sample_rate)
        self.preset_name = "Stream"

        self._running = False
        self._in_q: queue.Queue[np.ndarray] = queue.Queue(maxsize=8)
        self._out_q: queue.Queue[np.ndarray] = queue.Queue(maxsize=8)
        self._thread: threading.Thread | None = None
        self._in_stream = None
        self._out_stream = None
        self._in_channels = 1
        self._out_channels = 2
        self._latency_ms = 0.0
        self._cpu = 0.0
        self._underruns = 0
        self._dropped = 0
        self._last_error = ""
        self._input_name = ""
        self._output_name = ""

    # ------------------------------------------------------------------
    # Устройства
    # ------------------------------------------------------------------
    @staticmethod
    def available() -> bool:
        return sd is not None

    @staticmethod
    def import_error() -> str:
        return _SD_IMPORT_ERROR

    @staticmethod
    def list_devices() -> list[dict[str, Any]]:
        if sd is None:
            return []
        try:
            hostapis = sd.query_hostapis()
            devices = []
            for index, device in enumerate(sd.query_devices()):
                hostapi_index = int(device.get("hostapi", 0))
                hostapi = hostapis[hostapi_index]["name"] if hostapi_index < len(hostapis) else ""
                devices.append(
                    {
                        "index": index,
                        "name": str(device.get("name", "")),
                        "hostapi": str(hostapi),
                        "max_input_channels": int(device.get("max_input_channels", 0)),
                        "max_output_channels": int(device.get("max_output_channels", 0)),
                        "default_samplerate": float(device.get("default_samplerate", 48_000)),
                    }
                )
            return devices
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Не удалось получить список устройств: {exc}") from exc

    @classmethod
    def input_devices(cls) -> list[dict[str, Any]]:
        devices = [d for d in cls.list_devices() if d["max_input_channels"] > 0]
        return sorted(devices, key=lambda d: (0 if "WASAPI" in d["hostapi"].upper() else 1, d["name"].lower()))

    @classmethod
    def output_devices(cls) -> list[dict[str, Any]]:
        devices = [d for d in cls.list_devices() if d["max_output_channels"] > 0]
        return sorted(devices, key=lambda d: (0 if "WASAPI" in d["hostapi"].upper() else 1, d["name"].lower()))

    @classmethod
    def find_cable_output(cls) -> int | None:
        candidates = [
            d for d in cls.output_devices()
            if "cable input" in d["name"].lower()
        ]
        if not candidates:
            return None
        # WASAPI уже первый в списке.
        return int(candidates[0]["index"])

    @classmethod
    def default_input(cls) -> int | None:
        devices = cls.input_devices()
        if not devices:
            return None
        try:
            default = sd.default.device[0]
        except Exception:
            default = None
        # Для задержки предпочитаем WASAPI, даже если системный default — MME.
        if default is not None:
            for device in devices:
                if device["index"] == default and "WASAPI" in device["hostapi"].upper():
                    return int(default)
        return int(devices[0]["index"])

    @staticmethod
    def display_name(device: dict[str, Any]) -> str:
        return f'{device["name"]}  [{device["hostapi"]}]'

    # ------------------------------------------------------------------
    # Запуск / остановка
    # ------------------------------------------------------------------
    def start(self, input_device: int, output_device: int, blocksize: int | None = None) -> None:
        if sd is None:
            raise RuntimeError(
                "sounddevice не установлен. Выполните: pip install -r requirements.txt"
            )
        if self._running:
            self.stop()

        self.blocksize = int(blocksize or BLOCK_SIZE)
        self._in_q = queue.Queue(maxsize=8)
        self._out_q = queue.Queue(maxsize=8)
        for _ in range(2):
            self._out_q.put_nowait(np.zeros(self.blocksize, dtype=np.float32))

        self._underruns = 0
        self._dropped = 0
        self._last_error = ""
        self._cpu = 0.0
        self._latency_ms = 0.0
        self.chain.reset()
        self.analyzer.reset()

        self._input_name = str(sd.query_devices(input_device).get("name", ""))
        self._output_name = str(sd.query_devices(output_device).get("name", ""))

        self._running = True
        self._thread = threading.Thread(target=self._process_loop, name="tishina-dsp", daemon=True)
        self._thread.start()

        try:
            self._out_stream = self._open_output(output_device)
            self._in_stream = self._open_input(input_device)
            # Сначала микрофон, затем ждём, пока обработчик заполнит очередь.
            # Это убирает стартовые underrun'ы, когда вывод стартует раньше DSP.
            self._in_stream.start()
            deadline = time.monotonic() + 0.15
            while self._out_q.qsize() < 3 and time.monotonic() < deadline:
                time.sleep(0.005)
            self._out_stream.start()
        except Exception:
            self._running = False
            self._close_streams()
            raise

        self._latency_ms = self._estimate_latency()

    def stop(self) -> None:
        self._running = False
        self._close_streams()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._latency_ms = 0.0
        self._cpu = 0.0

    def _close_streams(self) -> None:
        for stream in (self._in_stream, self._out_stream):
            if stream is None:
                continue
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass
        self._in_stream = None
        self._out_stream = None

    def _open_input(self, device: int):
        last_error: Exception | None = None
        for channels in (1, 2):
            try:
                self._in_channels = channels
                return sd.InputStream(
                    device=int(device),
                    channels=channels,
                    samplerate=self.sample_rate,
                    blocksize=self.blocksize,
                    dtype="float32",
                    latency="low",
                    callback=self._input_callback,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(f"Не удалось открыть микрофон: {last_error}") from last_error

    def _open_output(self, device: int):
        last_error: Exception | None = None
        for channels in (2, 1):
            try:
                self._out_channels = channels
                return sd.OutputStream(
                    device=int(device),
                    channels=channels,
                    samplerate=self.sample_rate,
                    blocksize=self.blocksize,
                    dtype="float32",
                    latency="low",
                    callback=self._output_callback,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(
            "Не удалось открыть CABLE Input. Установлен ли VB-Cable? "
            f"Подробности: {last_error}"
        ) from last_error

    def _estimate_latency(self) -> float:
        total = self.blocksize / self.sample_rate
        for stream in (self._in_stream, self._out_stream):
            if stream is None:
                continue
            try:
                value = stream.latency
                total += sum(value) if isinstance(value, tuple) else float(value)
            except Exception:
                pass
        total += self._out_q.qsize() * self.blocksize / self.sample_rate
        return total * 1000.0

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _input_callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            self._last_error = f"input: {status}"
        try:
            if indata.ndim == 2 and indata.shape[1] > 1:
                frame = indata.mean(axis=1).astype(np.float32)
            else:
                frame = indata[:, 0].copy()
            self._push(self._in_q, frame)
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"input callback: {exc}"

    def _output_callback(self, outdata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            self._last_error = f"output: {status}"
        try:
            try:
                frame = self._out_q.get_nowait()
            except queue.Empty:
                self._underruns += 1
                outdata.fill(0.0)
                return

            if frame.size != frames:
                fixed = np.zeros(frames, dtype=np.float32)
                n = min(frames, frame.size)
                fixed[:n] = frame[:n]
                frame = fixed

            if outdata.shape[1] == 1:
                outdata[:, 0] = frame
            else:
                outdata[:] = frame[:, None]
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"output callback: {exc}"
            outdata.fill(0.0)

    def _process_loop(self) -> None:
        block_seconds = self.blocksize / self.sample_rate
        while self._running:
            try:
                frame = self._in_q.get(timeout=0.05)
            except queue.Empty:
                continue
            if frame is None:
                continue

            started = time.perf_counter()
            try:
                processed = self.chain.process(frame)
                self.analyzer.process_input(frame, self.chain.last_vad)
                self.analyzer.process_output(processed)
                self._push(self._out_q, processed)
            except Exception as exc:  # noqa: BLE001
                self._last_error = f"process: {exc}"
                self._push(self._out_q, frame)

            elapsed = time.perf_counter() - started
            load = elapsed / block_seconds if block_seconds > 0 else 0.0
            self._cpu = 0.9 * self._cpu + 0.1 * load

    def _push(self, target: queue.Queue, frame: np.ndarray) -> None:
        try:
            target.put_nowait(frame)
        except queue.Full:
            try:
                target.get_nowait()
            except queue.Empty:
                pass
            try:
                target.put_nowait(frame)
            except queue.Full:
                pass
            self._dropped += 1

    # ------------------------------------------------------------------
    # Управление
    # ------------------------------------------------------------------
    def set_bypass(self, value: bool) -> None:
        self.chain.set_bypass(value)

    def set_mute(self, value: bool) -> None:
        self.chain.gain.set_params(mute=bool(value))

    def set_preset(self, name: str) -> None:
        preset = load_preset(name)
        self.chain.apply_preset(preset)
        self.chain.reset()
        self.preset_name = name

    def set_module_param(self, module_name: str, key: str, value: Any) -> None:
        module = self.chain.module_by_name(module_name)
        if module is not None:
            module.set_params(**{key: value})

    def set_module_enabled(self, module_name: str, value: bool) -> None:
        self.chain.set_enabled(module_name, value)

    @property
    def running(self) -> bool:
        return self._running

    @property
    def preset(self) -> str:
        return self.preset_name

    def status(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "running": self._running,
            "input_name": self._input_name,
            "output_name": self._output_name,
            "latency_ms": self._latency_ms,
            "cpu_percent": self._cpu * 100.0,
            "underruns": self._underruns,
            "dropped": self._dropped,
            "last_error": self._last_error,
            "denoise_available": self.chain.denoise.available,
            "denoise_error": self.chain.denoise.last_error,
            "preset": self.preset_name,
        }
        data.update(self.analyzer.snapshot())
        return data
