param(
    [switch]$Reinstall
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python не найден в PATH. Установите Python 3.11/3.12 с python.org и включите Add Python to PATH."
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Создаю виртуальное окружение .venv ..."
    python -m venv .venv
}

$depsOk = $true
& $venvPython -c "import numpy, scipy, sounddevice, PySide6" 2>$null
if ($LASTEXITCODE -ne 0) { $depsOk = $false }

if ($Reinstall -or -not $depsOk) {
    Write-Host "Устанавливаю зависимости ..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
}

if (-not (Test-Path (Join-Path $root "tishina\vendor\rnnoise.dll"))) {
    Write-Host "Скачиваю RNNoise DLL ..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "setup_rnnoise.ps1")
}

Write-Host "Запускаю Тишину ..."
& $venvPython app.py
