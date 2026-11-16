[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

$starterRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'TrainingProcess.ps1')
$stateDirectory = Join-Path $starterRoot '.runtime_state'
$failureCount = 0

if (Test-Path -LiteralPath $stateDirectory) {
    foreach ($stateFile in @(Get-ChildItem -File -LiteralPath $stateDirectory -ErrorAction SilentlyContinue)) {
        try {
            $role = switch ($stateFile.Name) {
                'mcp-process.json' {'mcp'}
                'tunnel-process.json' {'tunnel'}
                default { throw 'Unknown state record; retain for diagnosis' }
            }
            $state=Get-TrainingProcessState $starterRoot $role
            if ($state.Status -ne 'Stopped') {
                Write-TrainingFail ('[FAIL] 실행 또는 식별 확인 필요: {0}' -f $role)
                $failureCount++
            }
            else {
                Remove-Item -LiteralPath $stateFile.FullName -Force
                Write-Host ('[PASS] 종료된 실행 기록 정리: {0}' -f $role)
            }
        }
        catch {
            Write-TrainingFail ('[FAIL] 상태 파일 확인 실패: {0}' -f $stateFile.Name)
            $failureCount++
        }
    }
}

# v2: .env 파일은 설계상 존재가 정상 — 자격증명 파일 검사 제거.
# 메모리 환경 변수 잔존만 확인.
$credentialVariables = @(
    'NW_IMAP_USER',
    'NW_IMAP_PASSWORD',
    'CONTROL_PLANE_TUNNEL_ID',
    'CONTROL_PLANE_API_KEY'
)
$remainingVariables = @($credentialVariables | Where-Object { -not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($_, 'Process')) })
if ($remainingVariables.Count -eq 0) {
    Write-Host '[PASS] 현재 점검 프로세스의 자격증명 환경 변수 없음'
}
else {
    Write-TrainingFail ('[FAIL] 자격증명 환경 변수 발견: {0}개' -f $remainingVariables.Count)
    $failureCount++
}

if ((Test-Path -LiteralPath $stateDirectory) -and -not (Get-ChildItem -Force -LiteralPath $stateDirectory -ErrorAction SilentlyContinue)) {
    Remove-Item -LiteralPath $stateDirectory -Force -ErrorAction SilentlyContinue
}

Write-Host '[INFO] SampleData의 수강자 산출물은 삭제하지 않았습니다.'
Write-Host '[ACTION] NAVER WORKS 임시보관 메일을 직접 삭제하십시오.'
Write-Host '[ACTION] OpenAI Platform에서 실습용 API Key를 Revoke하십시오.'

# v2: 자동 시작은 사용자가 ChatGPT 프롬프트로 Task Scheduler 작업을 등록하는 구조.
# 해제는 Task Scheduler GUI 또는 ChatGPT 프롬프트로 사용자가 직접 관리하므로 여기서 체크하지 않음.

if ($failureCount -eq 0) {
    Write-Host 'CLEANUP_RESULT: SUCCESS'
    exit 0
}

Write-TrainingFail ('CLEANUP_RESULT: FAIL ({0})' -f $failureCount)
exit 1
