[CmdletBinding()]
param([switch]$AllowManagedProcesses)

$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

$starterRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'TrainingProcess.ps1')
$resultPath = Join-Path $starterRoot 'precheck_result.txt'
$resultLines = New-Object System.Collections.Generic.List[string]
$failureCount = 0
$warningCount = 0

function Add-CheckResult {
    param(
        [ValidateSet('PASS', 'FAIL', 'WARN', 'INFO')]
        [string]$Status,
        [string]$Name,
        [string]$Detail = ''
    )

    $line = if ([string]::IsNullOrWhiteSpace($Detail)) {
        '[{0}] {1}' -f $Status, $Name
    }
    else {
        '[{0}] {1}: {2}' -f $Status, $Name, $Detail
    }

    Write-Host $line
    $resultLines.Add($line)
    if ($Status -eq 'FAIL') { $script:failureCount++ }
    if ($Status -eq 'WARN') { $script:warningCount++ }
}

function Test-TcpPort {
    param([string]$HostName, [int]$Port)

    try {
        return [bool](Test-NetConnection -ComputerName $HostName -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue)
    }
    catch {
        return $false
    }
}

Write-Host '업무자동화 실습 스타터킷 환경점검'
Write-Host '설치·다운로드·환경 설정 변경은 수행하지 않습니다.'
Write-Host ''

$resultLines.Add('업무자동화 실습 스타터킷 사전점검 결과')
$resultLines.Add(('점검 시각: {0}' -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss K')))

if ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) {
    Add-CheckResult PASS 'Windows 운영체제'
}
else {
    Add-CheckResult FAIL 'Windows 운영체제' 'Windows 전용 실습입니다.'
}

if ([Environment]::Is64BitOperatingSystem) {
    Add-CheckResult PASS 'Windows 64-bit'
}
else {
    Add-CheckResult FAIL 'Windows 64-bit' '64비트 운영체제가 필요합니다.'
}

if ($PSVersionTable.PSVersion -ge [version]'5.1') {
    Add-CheckResult PASS 'PowerShell' ('v{0}' -f $PSVersionTable.PSVersion)
}
else {
    Add-CheckResult FAIL 'PowerShell' ('v{0}; v5.1 이상 필요' -f $PSVersionTable.PSVersion)
}

try {
    $nodeCommand = Get-Command 'node.exe' -ErrorAction Stop
    $nodeVersionText = (& $nodeCommand.Source --version).TrimStart('v')
    $nodeVersion = [version]$nodeVersionText
    $nodeArchitecture = (& $nodeCommand.Source -p 'process.arch').Trim()

    if ($nodeVersion.Major -ge 24) {
        Add-CheckResult PASS 'Node.js v24 이상' ('v{0}' -f $nodeVersionText)
    }
    else {
        Add-CheckResult FAIL 'Node.js v24 이상' ('감지된 버전 v{0} — v24 이상 필요' -f $nodeVersionText)
    }

    if ($nodeArchitecture -eq 'x64') {
        Add-CheckResult PASS 'Node.js 64-bit' $nodeArchitecture
    }
    else {
        Add-CheckResult FAIL 'Node.js 64-bit' ('감지된 아키텍처 {0}' -f $nodeArchitecture)
    }
}
catch {
    Add-CheckResult FAIL 'Node.js' 'node.exe를 찾지 못했습니다.'
}

$requiredFiles = @(
    'START_HERE.cmd',
    'STOP_HERE.cmd',
    '.env',
    'AI_Scheduler_NAVERWORKS.vbs',
    'scripts\Start-TrainingConsole.ps1',
    'scripts\Stop-TrainingConsole.ps1',
    'scripts\Show-LatestLog.ps1',
    'scripts\TrainingProcess.ps1',
    'scripts\TrainingOutput.cs',
    'scripts\TrainingDebugLog.cs',
    'scripts\TrainingJob.cs',
    'VERSION.txt',
    'scripts\Start-StudentMcp.ps1',
    'scripts\Start-StudentTunnel.ps1',
    'scripts\Stop-StarterKitProcesses.ps1',
    'scripts\Test-StarterKitCleanup.ps1',
    'naverworks-mail-mcp\package.json',
    'naverworks-mail-mcp\package-lock.json',
    'naverworks-mail-mcp\src\server.mjs',
    'naverworks-mail-mcp\src\listen-training.mjs',
    'naverworks-mail-mcp\src\sender.mjs',
    'naverworks-mail-mcp\src\training-scope.mjs',
    'naverworks-mail-mcp\src\imap-errors.mjs',
    'naverworks-mail-mcp\src\config.mjs',
    'naverworks-mail-mcp\node_modules\dotenv\package.json',
    'naverworks-mail-mcp\node_modules\@modelcontextprotocol\sdk\package.json',
    'tunnel-client-v0.0.15\tunnel-client-runtime-cloudflared.exe',
    'tunnel-client-v0.0.15\LICENSE',
    'tunnel-client-v0.0.15\NOTICE',
    'tunnel-client-v0.0.15\tunnel-client-runtime-cloudflared-v0.0.15-windows-amd64-licenses.txt',
    'tunnel-client-v0.0.15\tunnel-client-runtime-cloudflared-v0.0.15-windows-amd64.spdx.json',
    'SampleData\매출_서울지점_2026-05.xlsx',
    'SampleData\매출_부산지점_2026-05.xlsx',
    'SampleData\매출_대구지점_2026-05.xlsx',
    'SampleData\매출_인천지점_2026-05.xlsx'
)

$missingFiles = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $starterRoot $_) -PathType Leaf) })
if ($missingFiles.Count -eq 0) {
    Add-CheckResult PASS '스타터킷 필수 파일' ('{0}개' -f $requiredFiles.Count)
}
else {
    Add-CheckResult FAIL '스타터킷 필수 파일' ('누락 {0}개' -f $missingFiles.Count)
    foreach ($missingFile in $missingFiles) {
        Add-CheckResult INFO '누락 파일' $missingFile
    }
}

$writeTestPath = Join-Path $starterRoot ('.write-test-{0}.tmp' -f [guid]::NewGuid().ToString('N'))
try {
    [IO.File]::WriteAllText($writeTestPath, 'ok', $utf8NoBom)
    Remove-Item -LiteralPath $writeTestPath -Force
    Add-CheckResult PASS '스타터킷 폴더 쓰기 권한'
}
catch {
    Add-CheckResult FAIL '스타터킷 폴더 쓰기 권한' '쓰기 가능한 로컬 폴더로 이동하십시오.'
}
finally {
    Remove-Item -LiteralPath $writeTestPath -Force -ErrorAction SilentlyContinue
}

if ($starterRoot -match '(?i)\\OneDrive\\|\\Downloads\\|^\\\\') {
    Add-CheckResult WARN '권장 설치 위치' '바탕화면 AI실습 폴더처럼 동기화·공유되지 않는 로컬 폴더 사용을 권장합니다.'
}
else {
    Add-CheckResult PASS '권장 설치 위치'
}

foreach ($role in @('mcp','tunnel')) {
    $identity=Get-TrainingProcessState $starterRoot $role
    if ($identity.Status -in @('Conflict','Orphaned')) {
        Add-CheckResult FAIL ($role + ' 실행 상태') '강사 확인 필요'
        continue
    }
    if ($AllowManagedProcesses -and $identity.Status -eq 'Running') {
        Add-CheckResult PASS ($role + ' 실행 환경') '기존 실행 상태는 시작 단계에서 재확인'
        continue
    }
    $available=@(Get-TrainingPorts $role | Where-Object { Test-TrainingPortAvailable $_ })
    if ($available.Count -gt 0) { Add-CheckResult PASS ($role + ' 실행 환경') '사용 가능; 실제 시작 시 확정' }
    else { Add-CheckResult FAIL ($role + ' 실행 환경') '모든 연결 후보를 사용할 수 없습니다. 강사 확인 필요' }
}

$networkChecks = @(
    @{Name='NAVER WORKS IMAP'; HostName='imap.worksmobile.com'; Port=993},
    @{Name='OpenAI Tunnel 제어 경로'; HostName='api.openai.com'; Port=443},
    @{Name='ChatGPT 웹'; HostName='chatgpt.com'; Port=443},
    @{Name='OpenAI Platform'; HostName='platform.openai.com'; Port=443}
)
foreach ($networkCheck in $networkChecks) {
    if (Test-TcpPort -HostName $networkCheck.HostName -Port $networkCheck.Port) {
        Add-CheckResult PASS $networkCheck.Name '통신 가능'
    }
    else {
        Add-CheckResult FAIL $networkCheck.Name '연결 실패'
    }
}
Add-CheckResult INFO 'Cloudflare Edge 연결' '교육장 네트워크에서 강사 실Tunnel 사전 검증 필요'

# v2: .env 파일이 있어야 자동 실행 가능 (v1과 정반대)
$envFile = Join-Path $starterRoot '.env'
if (Test-Path -LiteralPath $envFile -PathType Leaf) {
    Add-CheckResult PASS '.env 파일 존재'
}
else {
    Add-CheckResult FAIL '.env 파일 없음' '.env.example을 복사·편집하여 .env로 저장하세요.'
}

Write-Host ''
if ($failureCount -eq 0) {
    # Wording follows the course material (교안 Chap 1 ✅1); PRECHECK_RESULT stays machine-readable.
    Write-Host '[OK] 환경 점검 통과'
    Write-Host 'PRECHECK_RESULT: PASS'
    $resultLines.Add('[OK] 환경 점검 통과')
    $resultLines.Add('PRECHECK_RESULT: PASS')
    $exitCode = 0
}
else {
    Write-TrainingFail ('[FAIL] 점검 실패 {0}건, 경고 {1}건' -f $failureCount, $warningCount)
    Write-TrainingFail 'PRECHECK_RESULT: FAIL'
    $resultLines.Add(('[FAIL] 점검 실패 {0}건, 경고 {1}건' -f $failureCount, $warningCount))
    $resultLines.Add('PRECHECK_RESULT: FAIL')
    $exitCode = 1
}

[IO.File]::WriteAllLines($resultPath, $resultLines, $utf8NoBom)
exit $exitCode
