# Show-LatestLog.ps1 — FAIL 발생 시 최신 logs/*.txt를 보여주고 Enter 대기.
# .vbs에서 -File 로 호출. 한글 리터럴은 이 파일 안에만 두어 콘솔 인코딩 손실을 피함.

[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)

$logsDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'logs'
$log = Get-ChildItem -LiteralPath $logsDir -Filter '*.txt' -File -ErrorAction SilentlyContinue |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($log) {
    Write-Host (Get-Content -LiteralPath $log.FullName -Raw -Encoding UTF8)
} else {
    Write-Host '[INFO] logs 폴더에 파일 없음'
}

Write-Host ''
Write-Host '[FAIL] 위 로그를 강사에게 공유하세요. Enter로 창 닫기.'
Read-Host | Out-Null