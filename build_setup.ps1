# Сборка установщика TishinaSetup.exe.
# Требуется Inno Setup 6 (ISCC.exe) и уже собранная папка dist\Tishina.

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$iss = Join-Path $root "installer\Tishina.iss"
$appExe = Join-Path $root "dist\Tishina\Tishina.exe"
$setupExe = Join-Path $root "dist_installer\TishinaSetup.exe"

if (-not (Test-Path $iss)) {
    throw "Не найден сценарий установщика: $iss"
}
if (-not (Test-Path $appExe)) {
    throw "Сначала соберите приложение: powershell -ExecutionPolicy Bypass -File .\build.ps1"
}

$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
) | Where-Object { $_ -and (Test-Path $_) }

$iscc = $isccCandidates | Select-Object -First 1
if (-not $iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}
if (-not $iscc) {
    throw "Не найден Inno Setup 6 (ISCC.exe). Установите: winget install JRSoftware.InnoSetup"
}

Write-Host "Inno Setup: $iscc"
Write-Host "Приложение: $appExe"

& $iscc /Qp $iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup завершился с кодом $LASTEXITCODE"
}
if (-not (Test-Path $setupExe)) {
    throw "Установщик не создан: $setupExe"
}

$item = Get-Item $setupExe
Write-Host ("Готово: {0} ({1:N1} МБ)" -f $item.FullName, ($item.Length / 1MB))
