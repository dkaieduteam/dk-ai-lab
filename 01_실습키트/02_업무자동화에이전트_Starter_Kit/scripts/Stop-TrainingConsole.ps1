[CmdletBinding()]
param()

# Case_배포용_v2 Stop-TrainingConsole — STOP_HERE.cmd가 호출하는 wrapper.
# 역할: logs/에 console transcript 캡처 + Stop-StarterKitProcesses + Test-StarterKitCleanup 순차 실행.

$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$consoleRoot = Split-Path -Parent $PSScriptRoot
$consoleScripts = $PSScriptRoot

# logs/ 폴더 보장
$logsDir = Join-Path $consoleRoot 'logs'
if (-not (Test-Path -LiteralPath $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
$transcriptPath = Join-Path $logsDir ('{0:yyyy-MM-dd HHmmss} stop.txt' -f (Get-Date))
try { Start-Transcript -Path $transcriptPath -Force | Out-Null } catch { Write-Host ('[INFO] Transcript 시작 실패 — 계속 진행: {0}' -f $_.Exception.Message) }

$stopExit = 1
$cleanExit = 1
try {
    Write-Host ''
    Write-Host '--- Stop-StarterKitProcesses ---'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $consoleScripts 'Stop-StarterKitProcesses.ps1')
    $stopExit = $LASTEXITCODE

    Write-Host ''
    Write-Host '--- Test-StarterKitCleanup ---'
    & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $consoleScripts 'Test-StarterKitCleanup.ps1')
    $cleanExit = $LASTEXITCODE

    Write-Host ''
    if ($stopExit -eq 0 -and $cleanExit -eq 0) {
        Write-Host '[DONE] 로컬 정리 완료.'
    }
    else {
        Write-Host ('[FAIL] 정리 중 문제 발생 — stop_exit={0}, clean_exit={1}' -f $stopExit, $cleanExit)
    }
}
finally {
    try { Stop-Transcript | Out-Null } catch { }
}

# 최종 종료 코드: cleanup 결과 기준
exit $cleanExit
