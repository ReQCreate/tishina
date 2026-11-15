$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$vendor = Join-Path $root "tishina\vendor"
$dest = Join-Path $vendor "rnnoise.dll"
$licenseDest = Join-Path $vendor "PYRNNOISE_LICENSE.txt"

if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 1MB)) {
    Write-Host "RNNoise DLL уже на месте: $dest"
    exit 0
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
    # Старые версии PowerShell могут не знать Tls12 — пробуем без явной настройки.
}

New-Item -ItemType Directory -Force -Path $vendor | Out-Null
$tmp = Join-Path $env:TEMP "tishina_rnnoise"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

Write-Host "Получаю информацию о pyrnnoise с PyPI ..."
$json = Invoke-RestMethod -Uri "https://pypi.org/pypi/pyrnnoise/json" -UseBasicParsing
$wheel = $json.urls | Where-Object { $_.filename -like "*win_amd64.whl" } | Select-Object -First 1
if (-not $wheel) {
    throw "Не найден win_amd64 wheel pyrnnoise. Проверьте https://pypi.org/project/pyrnnoise/"
}

$whlPath = Join-Path $tmp $wheel.filename
Write-Host "Скачиваю $($wheel.filename) ..."
Invoke-WebRequest -Uri $wheel.url -OutFile $whlPath -UseBasicParsing

$zipPath = "$whlPath.zip"
Copy-Item $whlPath $zipPath -Force
$extract = Join-Path $tmp "extract"
Expand-Archive -Path $zipPath -DestinationPath $extract -Force

$dll = Get-ChildItem -Path $extract -Recurse -Filter "rnnoise.dll" | Select-Object -First 1
if (-not $dll) {
    throw "В wheel не найден rnnoise.dll"
}
Copy-Item $dll.FullName $dest -Force

$license = Get-ChildItem -Path $extract -Recurse -Filter "LICENSE" | Select-Object -First 1
if ($license) {
    Copy-Item $license.FullName $licenseDest -Force
}

Remove-Item -Recurse -Force $tmp
Write-Host "Готово: $dest"
Write-Host "RNNoise распространяется по лицензии BSD-3-Clause; обёртка pyrnnoise — Apache-2.0."
