[CmdletBinding()]
param()

# Case_배포용_v2 Start-TrainingConsole — 메뉴 없음(자동 흐름).
# 흐름: 환경 점검 → MCP 시작 → Tunnel 시작 → 대기. 종료는 STOP_HERE.cmd가 담당.

$ErrorActionPreference = 'Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$consoleRoot = Split-Path -Parent $PSScriptRoot
$consoleScripts = $PSScriptRoot

# 중복 실행 방지(세션 단위)
$script:singletonMutex = New-Object System.Threading.Mutex($false, 'AIEduStarterKitTrainingConsole')
if (-not $script:singletonMutex.WaitOne(0)) {
    Write-Host '[INFO] 다른 창에서 이미 실행 중이므로 이 창을 닫습니다. (10초 뒤 자동 종료)'
    Start-Sleep -Seconds 10
    exit 0
}

. (Join-Path $consoleScripts 'TrainingProcess.ps1')

# 콘솔 전체 출력을 logs/ 폴더에 캡처 (server.mjs 시작 전 단계의 실패도 로그로 남게)
$logsDir = Join-Path $consoleRoot 'logs'
if (-not (Test-Path -LiteralPath $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
$transcriptPath = Join-Path $logsDir ('{0:yyyy-MM-dd HHmmss} console.txt' -f (Get-Date))
try { Start-Transcript -Path $transcriptPath -Force | Out-Null } catch { Write-Host ('[INFO] Transcript 시작 실패 — 계속 진행: {0}' -f $_.Exception.Message) }

function Invoke-TrainingCheck {
    param([string]$ScriptName, [string[]]$Options=@(), [switch]$Quiet, [string]$HidePattern='')
    $lines = @(& powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $consoleScripts $ScriptName) @Options |
        ForEach-Object {
            $line = "$_"
            if (-not $Quiet -and -not ($HidePattern -and $line -match $HidePattern)) { Write-Host $line }
            $line
        })
    $passed = ($LASTEXITCODE -eq 0)
    if ($Quiet -and -not $passed) {
        foreach ($line in $lines) { if (-not ($HidePattern -and $line -match $HidePattern)) { Write-Host $line } }
    }
    return $passed
}

function Show-EnvSummary {
    # .env 로드 결과를 민감 값 마스킹 상태로 요약 출력(파일은 config.mjs가 재검증).
    param([string]$EnvPath)
    if (-not (Test-Path -LiteralPath $EnvPath)) {
        Write-Host '[FAIL] .env 파일을 찾을 수 없습니다. Starter_kit 폴더에 .env를 두세요.'
        return $false
    }
    $envVars = @{}
    Get-Content -LiteralPath $EnvPath -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        $eq = $line.IndexOf('=')
        if ($eq -le 0) { return }
        $key = $line.Substring(0, $eq).Trim()
        $value = $line.Substring($eq + 1).Trim()
        if ($value.StartsWith('"') -and $value.EndsWith('"')) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $envVars[$key] = $value
    }
    function Mask-Short { param($s, [int]$keep=10)
        if (-not $s) { return '(empty)' }
        if ($s.Length -le $keep) { return ('*' * $s.Length) }
        return ($s.Substring(0, $keep) + '*****')
    }
    $nwId = $envVars['NW_ID']
    $nwIdMasked = if ($nwId -and $nwId.Contains('@')) {
        $local = $nwId.Split('@')[0]
        $domain = $nwId.Substring($nwId.IndexOf('@'))
        if ($local.Length -le 2) { ('*' * $local.Length) + $domain } else { $local.Substring(0, 2) + '***' + $domain }
    } else { '(empty)' }
    Write-Host '--- .env 로드 요약 ---'
    Write-Host ('  NW_ID            : {0}' -f $nwIdMasked)
    Write-Host ('  NW_PW            : {0}' -f $(if ($envVars['NW_PW']) { '***' } else { '(empty)' }))
    Write-Host ('  TUNNEL_ID        : {0}' -f (Mask-Short $envVars['TUNNEL_ID'] 10))
    Write-Host ('  API_KEY          : {0}' -f $(if ($envVars['API_KEY']) { 'sk-********' } else { '(empty)' }))
    $folder = $envVars['NW_MAIL_FOLDER']
    Write-Host ('  NW_MAIL_FOLDER   : {0}' -f $(if ($folder) { $folder } else { '(empty)' }))
    $prefix = $envVars['NW_MAIL_PREFIX']
    Write-Host ('  NW_MAIL_PREFIX   : {0}' -f $(if ($prefix) { $prefix } else { '(empty · 폴더 내 전체 조회)' }))
    $maxCount = $envVars['MCP_MAX_COUNT']
    Write-Host ('  MCP_MAX_COUNT    : {0}' -f $(if ($maxCount) { $maxCount } else { '50(default)' }))
    $days = $envVars['MCP_DAYS']
    Write-Host ('  MCP_DAYS         : {0}' -f $(if ($days) { $days } else { '30(default)' }))
    $maxMb = $envVars['MCP_MAX_MESSAGE_MB']
    Write-Host ('  MCP_MAX_MESSAGE_MB: {0}' -f $(if ($maxMb) { ('{0} MB' -f $maxMb) } else { '10 MB(default)' }))
    Write-Host ''
    return $true
}

function Invoke-TrainingAutoFlow {
    Write-Host ''
    Write-Host '========================================='
    Write-Host '업무자동화 에이전트 실습 (v2 자동 흐름)'
    Write-Host '========================================='
    Write-Host ''

    # 1) 환경 점검
    Write-Host '[STEP 1/4] 환경 점검...'
    $envPassed = Invoke-TrainingCheck 'Test-StarterKitEnvironment.ps1' @('-AllowManagedProcesses') -Quiet -HidePattern '^PRECHECK_RESULT:'
    if (-not $envPassed) {
        Write-Host '[FAIL] 환경 점검 실패. 해결 후 다시 START_HERE.cmd를 실행하세요.'
        throw 'ENV_CHECK_FAILED'
    }
    Write-Host '[OK] 환경 점검 통과'
    Write-Host ''

    # 2) .env 요약
    Write-Host '[STEP 2/4] .env 로드...'
    $envPath = Join-Path $consoleRoot '.env'
    if (-not (Show-EnvSummary $envPath)) {
        throw 'ENV_FILE_MISSING'
    }

    # 3) MCP 시작
    Write-Host '[STEP 3/4] 로컬 MCP 서버 시작...'
    if ((Get-TrainingProcessState $consoleRoot 'mcp').Status -eq 'Running') {
        Write-Host '[OK] 기존 MCP 재사용 — PID 유지'
    }
    else {
        & (Join-Path $consoleScripts 'Start-StudentMcp.ps1') -Managed
    }
    if (-not (Test-TrainingReady $consoleRoot 'mcp')) {
        throw (New-TrainingFailureMessage 'mcp' 'MCP_NOT_READY_AFTER_START' (Get-TrainingLatestLog $consoleRoot 'mcp'))
    }
    Write-Host '[OK] MCP 서버 준비 완료'
    Write-Host ''

    # 4) Tunnel 시작
    Write-Host '[STEP 4/4] Tunnel 연결 시작...'
    if ((Get-TrainingProcessState $consoleRoot 'tunnel').Status -eq 'Running') {
        if (-not (Test-TrainingTunnelTarget $consoleRoot)) {
            if (-not (Stop-TrainingRole $consoleRoot 'tunnel')) {
                throw (New-TrainingFailureMessage 'tunnel' 'STALE_TUNNEL_CLEANUP_REQUIRED' '')
            }
            Write-Host '[INFO] 변경된 MCP에 연결하기 위해 기존 Tunnel을 정리했습니다.'
        }
        elseif (Test-TrainingReady $consoleRoot 'tunnel') {
            Write-Host '[READY] 요청 대기 중 (이미 연결됨)'
            return
        }
    }
    & (Join-Path $consoleScripts 'Start-StudentTunnel.ps1') -Managed
    if (-not (Test-TrainingReady $consoleRoot 'tunnel')) {
        throw (New-TrainingFailureMessage 'tunnel' 'TUNNEL_NOT_READY_AFTER_START' (Get-TrainingLatestLog $consoleRoot 'tunnel'))
    }
    Write-Host '[OK] Tunnel 연결 완료'
    Write-Host ''
    Write-Host '[READY] 실습 준비 완료 — ChatGPT에서 MCP 커넥터로 접속하세요.'
    Write-Host '이 창은 유지하세요. 종료는 STOP_HERE.cmd 또는 창 닫기를 사용하세요.'
    Write-Host ''
    # 대기 — 자식 프로세스(MCP/Tunnel)가 돌아가는 동안 콘솔 유지.
    # STOP_HERE가 자식을 종료시킬 때 빠르게 반응하도록 5초 주기로 폴링.
    while ($true) {
        Start-Sleep -Seconds 5
        $mcpAlive = (Get-TrainingProcessState $consoleRoot 'mcp').Status -eq 'Running'
        $tunnelAlive = (Get-TrainingProcessState $consoleRoot 'tunnel').Status -eq 'Running'
        if (-not $mcpAlive -or -not $tunnelAlive) {
            Write-Host ('[STOP] 자식 프로세스 상태 — MCP={0}, Tunnel={1}' -f $mcpAlive, $tunnelAlive)
            break
        }
    }
}

function Show-TrainingConsoleFailure {
    param($ErrorRecord, [string]$DefaultRole='')
    $info = ConvertFrom-TrainingFailure ([string]$ErrorRecord.Exception.Message) $DefaultRole
    Write-Host ''
    Show-TrainingFailure $info.Role $info.Code
    $logPath = $info.LogPath
    if ([string]::IsNullOrEmpty($logPath) -and $info.Role -in @('mcp','tunnel') -and
        $info.Code -notin @('STATE_CONFLICT','OPERATION_IN_PROGRESS')) {
        $logPath = Get-TrainingLatestLog $consoleRoot $info.Role
    }
    if (-not [string]::IsNullOrEmpty($logPath)) { Show-TrainingLogTail $logPath }
}

# 전역 mutex
$sha = [Security.Cryptography.SHA256]::Create()
try { $rootHash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($consoleRoot.ToLowerInvariant()))).Replace('-','') }
finally { $sha.Dispose() }
$mutex = New-Object Threading.Mutex($false, ('Local\AITraining-' + $rootHash))
$locked = $false
$script:exitCode = 0
try {
    try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) {
        Write-Host '[INFO] 이 스타터킷은 이미 다른 창에서 실행 중입니다.'
        return
    }
    try {
        Invoke-TrainingAutoFlow
    }
    catch {
        Show-TrainingConsoleFailure $_
        Write-TrainingFail '[FAIL] 자동 흐름 중단. 로그를 확인한 뒤 STOP_HERE.cmd로 정리하고 다시 START_HERE.cmd를 실행하세요.'
        Start-Sleep -Seconds 5
        $script:exitCode = 1
    }
}
finally {
    $wasLocked = $locked
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
    foreach ($name in @('NW_IMAP_USER','NW_IMAP_PASSWORD','CONTROL_PLANE_TUNNEL_ID','CONTROL_PLANE_API_KEY')) {
        [Environment]::SetEnvironmentVariable($name, $null, 'Process')
    }
    # 창 정상 종료(X·Ctrl+C) 또는 자식 프로세스 소멸 시 자동 cleanup.
    # 이 세션이 실제로 Mutex를 쥐었던 경우에만 실행 (다른 창의 세션을 건드리지 않음).
    # Task Scheduler 강제 Terminate는 finally를 못 타므로 Job Object의 KILL_ON_JOB_CLOSE에 의존.
    if ($wasLocked) {
        try {
            Write-Host ''
            Write-Host '[INFO] 자동 cleanup — 자식 프로세스 정리'
            & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $consoleScripts 'Stop-StarterKitProcesses.ps1')
        } catch { Write-Host ('[WARN] 자동 cleanup 실패: {0}' -f $_.Exception.Message) }
    }
    try { Stop-Transcript | Out-Null } catch { }
}

# Task Scheduler/.bat이 FAIL 여부 판정에 쓰도록 종료코드 명시 (정상 종료=0, 자동 흐름 실패=1).
exit $script:exitCode
