param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python не найден в PATH."
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Создаю виртуальное окружение .venv ..."
    python -m venv .venv
}

Write-Host "Устанавливаю зависимости для сборки ..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements-dev.txt

if (-not (Test-Path (Join-Path $root "tishina\vendor\rnnoise.dll"))) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "setup_rnnoise.ps1")
}

if ($Clean) {
    Remove-Item -Recurse -Force (Join-Path $root "build") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force (Join-Path $root "dist") -ErrorAction SilentlyContinue
}

Write-Host "Собираю Tishina.exe ..."
& $venvPython -m PyInstaller --noconfirm Tishina.spec

Write-Host ""
Write-Host "Готово: dist\Tishina\Tishina.exe"
Write-Host "VB-Cable устанавливается отдельно и в сборку не входит."
