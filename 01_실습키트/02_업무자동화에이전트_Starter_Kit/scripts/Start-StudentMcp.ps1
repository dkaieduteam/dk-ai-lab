[CmdletBinding()]
param([switch]$Managed)
# -Managed : called from START_HERE (Start-TrainingConsole.ps1). Failures are thrown to the console.
# no switch: MCP-only window (부록_상시자동화\START_MCP_ONLY.cmd). The window stays open while MCP runs;
#            closing it (X / Ctrl+C) stops the MCP that this window started.
# Screen wording follows the course material (교안 Chap 1 ✅2). Local ports are never shown on screen.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$starterRoot=Split-Path -Parent $PSScriptRoot
$appRoot=Join-Path $starterRoot 'naverworks-mail-mcp'
. (Join-Path $PSScriptRoot 'TrainingProcess.ps1')
$securePassword=$null
$child=$null
$ready=$false
$failed=$false
$failCode=$null
$launchLock=$null
$job=$null
$reused=$false
$port=0

# Diagnostic log (.diagnostics\mcp-debug-*.log). ID/password are registered as secrets and masked;
# server.mjs itself writes metadata only (no credentials, no mail content).
$debugLog=$null
try {
    if (-not ('TrainingDebugLog' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'TrainingDebugLog.cs') }
    $debugLog=New-Object TrainingDebugLog((Join-Path $starterRoot ('.diagnostics\mcp-debug-{0:yyyyMMdd-HHmmss}.log' -f (Get-Date))))
}
catch { Write-Host '[INFO] 진단 로그 파일을 만들지 못했습니다. 실행은 계속합니다.' }

function Write-McpLog {
    param([string]$Message)
    if ($null -ne $script:debugLog) { $script:debugLog.Write('STEP', $Message) }
}

function Show-McpScope {
    # v2: 서버의 안전 경계는 .env + config.mjs가 결정. server.mjs 로그에서 실제 값 확인.
    Write-Host 'SCOPE: .env의 NW_MAIL_FOLDER·NW_MAIL_PREFIX·MCP_MAX_COUNT·MCP_DAYS 기준'
    Write-Host '       (실제 적용 값은 MCP 서버 시작 로그에 출력됨)'
}

function Get-McpReuseResult {
    # Reuses an MCP started by START_HERE or another MCP-only window instead of starting a duplicate.
    $state=Get-TrainingProcessState $starterRoot 'mcp'
    Write-McpLog ('mcp_state={0}' -f $state.Status)
    if ($state.Status -eq 'Conflict') { throw 'STATE_CONFLICT' }
    if ($state.Status -ne 'Running') { return $false }
    if (-not (Wait-TrainingReady $starterRoot 'mcp' 10)) { throw 'RUNNING_NOT_READY' }
    Write-McpLog ('reuse pid={0} port={1}' -f $state.Data.pid, $state.Data.activePort)
    Write-Host '[OK] 기존 MCP 재사용 — PID 유지'
    if (-not $Managed) {
        Show-McpScope
        Write-Host '[READY] MCP 준비 완료'
        Write-Host ''
        Write-Host '[INFO] START_HERE 또는 다른 창에서 시작한 MCP를 그대로 사용합니다. 중복 실행하지 않았습니다.'
        Write-Host '[INFO] 이 창은 닫아도 됩니다. 실행 중인 MCP는 그대로 유지되며 종료는 START_HERE.cmd 3번을 사용하십시오.'
    }
    return $true
}

function Watch-McpMailResults {
    # MCP-only window: shows each mail search/read result as it happens (codes only, no mail content).
    param($Process, [string]$LogPath)
    $shown=0; $previous=''
    while (-not $Process.WaitForExit(1000)) {
        $results=@(Get-TrainingMailResults (Read-TrainingLogText $LogPath))
        for ($i=$shown; $i -lt $results.Count; $i++) {
            $key=('{0}|{1}' -f $results[$i].Result, $results[$i].Code)
            if ($key -ne $previous) { Show-TrainingMailResult $results[$i] }
            $previous=$key
        }
        $shown=$results.Count
    }
}

if (-not $Managed) {
    Write-Host '업무자동화 에이전트 실습 - 로컬 MCP 서버 (v2 .env-driven)'
    Write-Host '----------------------------------------'
    Write-Host 'Starter_kit/.env 파일의 NW_ID·NW_PW 값으로 자동 로그인합니다.'
    Write-Host ''
}

$kitVersion=(Get-Content -LiteralPath (Join-Path $starterRoot 'VERSION.txt') -ErrorAction SilentlyContinue | Select-String '^STARTER_KIT_VERSION=') -join ''
Write-McpLog ('START kit={0} ps={1} os={2} managed={3}' -f $kitVersion, $PSVersionTable.PSVersion, [Environment]::OSVersion.VersionString, [bool]$Managed)
try {
    # 1) Reuse first: no sign-in prompt when MCP is already running.
    if (Get-McpReuseResult) { $reused=$true; $ready=$true; return }

    # 2) Local prerequisites before asking for the password.
    try { $node=Get-Command node.exe -ErrorAction Stop } catch { throw 'NODE_MISSING' }
    $nodeVersion=(& $node.Source --version).TrimStart('v')
    Write-McpLog ('node path="{0}" version={1}' -f $node.Source, $nodeVersion)
    if (([version]$nodeVersion).Major -lt 24) { throw 'NODE_VERSION' }
    if (-not (Test-Path (Join-Path $appRoot 'node_modules\@modelcontextprotocol\sdk\package.json'))) { throw 'DEPENDENCIES' }
    $freePorts=@(Get-TrainingPorts 'mcp' | Where-Object { Test-TrainingPortAvailable $_ })
    Write-McpLog ('port_precheck free={0}' -f ($freePorts -join ','))
    # Do not ask for the password when no candidate port can be used.
    if ($freePorts.Count -eq 0) { throw 'MCP_PORTS_UNAVAILABLE' }

    # 3) v2: Load credentials from .env (replaces interactive prompt + 5-retry loop)
    #    probe-imap.mjs exit codes:
    #      - 0  = SUCCESS → proceed
    #      - 10 = IMAP_AUTH_FAILED
    #      - 11 = IMAP_ACCESS_NOT_ALLOWED
    #      - 12~16 = network/server failure
    $envFile = Join-Path $starterRoot '.env'
    if (-not (Test-Path -LiteralPath $envFile)) {
        Write-TrainingFail '[FAIL] .env 파일이 없습니다. Starter_kit 폴더에 .env를 저장해 주세요.'
        throw 'ENV_FILE_MISSING'
    }
    $envVars = @{}
    Get-Content -LiteralPath $envFile -Encoding UTF8 | ForEach-Object {
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
    $userName = $envVars['NW_ID']
    $plainPassword = $envVars['NW_PW']
    if ([string]::IsNullOrWhiteSpace($userName)) {
        Write-TrainingFail '[FAIL] .env의 NW_ID 값이 비어 있습니다.'
        throw 'NW_ID_EMPTY'
    }
    if ([string]::IsNullOrEmpty($plainPassword) -or $plainPassword -match '^\*+.*\*+$') {
        Write-TrainingFail '[FAIL] .env의 NW_PW 값이 비어 있거나 강사 제공 값으로 교체되지 않았습니다.'
        throw 'NW_PW_EMPTY'
    }
    if ($null -ne $debugLog) { $debugLog.AddSecret($userName); $debugLog.AddSecret($plainPassword) }
    Write-McpLog ('env_load id_len={0} id_has_at={1} password_len={2}' -f $userName.Length,
        $(if ($userName -match '@') {'YES'} else {'NO'}), $plainPassword.Length)

    Write-Host '[INFO] NAVER WORKS 로그인 확인 중...'
    $probeScript = Join-Path $appRoot 'src\probe-imap.mjs'
    $env:NW_IMAP_USER = $userName
    $env:NW_IMAP_PASSWORD = $plainPassword
    $probeErrFile = [IO.Path]::GetTempFileName()
    $probeOutFile = [IO.Path]::GetTempFileName()
    try {
        $probeProcess = Start-Process -FilePath $node.Source -ArgumentList ('"{0}"' -f $probeScript) -NoNewWindow -Wait -PassThru -RedirectStandardError $probeErrFile -RedirectStandardOutput $probeOutFile
        $probeExit = $probeProcess.ExitCode
    }
    finally {
        Remove-Item $probeErrFile, $probeOutFile -Force -ErrorAction SilentlyContinue
        Remove-Item Env:NW_IMAP_USER, Env:NW_IMAP_PASSWORD -ErrorAction SilentlyContinue
    }
    Write-McpLog ('probe exit={0}' -f $probeExit)
    if ($probeExit -ne 0) {
        $code = switch ($probeExit) {
            10 { 'IMAP_AUTH_FAILED' }
            11 { 'IMAP_ACCESS_NOT_ALLOWED' }
            12 { 'IMAP_CONNECTION_FAILED' }
            13 { 'IMAP_DNS_FAILED' }
            14 { 'IMAP_TIMEOUT' }
            15 { 'IMAP_TLS_FAILED' }
            16 { 'IMAP_SERVER_REJECTED' }
            2  { 'MISSING_IMAP_CREDENTIALS' }
            default { 'UNEXPECTED_ERROR' }
        }
        Write-TrainingFail ('[FAIL] NAVER WORKS 로그인 실패 ({0}) — .env의 NW_ID/NW_PW 값을 확인해 주세요.' -f $code)
        throw $code
    }
    Write-Host '[OK] NAVER WORKS 로그인 확인 완료 — MCP 서버를 시작합니다.'

    # 4) Start under the lock; re-check because another window may have started MCP meanwhile.
    $launchLock=Enter-TrainingLaunchLock $starterRoot 'mcp'
    if (Get-McpReuseResult) { $reused=$true; $ready=$true; return }
    # A stale Tunnel must not continue pointing at a replacement MCP.
    if (-not (Stop-TrainingRole $starterRoot 'tunnel')) { throw 'TUNNEL_CLEANUP_REQUIRED' }
    if (-not (Stop-TrainingRole $starterRoot 'mcp')) { throw 'STATE_CLEANUP_REQUIRED' }
    Write-Host '로컬 MCP를 시작합니다.'
    $env:NW_IMAP_USER=$userName
    $env:NW_IMAP_PASSWORD=$plainPassword
    Write-McpLog 'launch node src\server.mjs'
    $child=Start-TrainingChild $node.Source ('"{0}"' -f (Join-Path $appRoot 'src\server.mjs')) $appRoot '' $debugLog
    Write-McpLog ('node_pid={0}' -f $child.Process.Id)
    if (-not $Managed) {
        # Window lifetime = MCP lifetime (see header). Failure only means X may leave MCP running.
        try {
            if (-not ('TrainingJob' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'TrainingJob.cs') }
            $job=New-Object TrainingJob
            Write-McpLog ('job_assign={0}' -f $job.Assign($child.Process))
        }
        catch { Write-McpLog ('job_assign=FAIL type={0}' -f $_.Exception.GetType().FullName) }
    }
    Save-TrainingProcessState $starterRoot 'mcp' $child.Process
    Remove-Item Env:NW_IMAP_USER,Env:NW_IMAP_PASSWORD -ErrorAction SilentlyContinue
    $userName=$null; $plainPassword=$null
    $watch=[Diagnostics.Stopwatch]::StartNew()
    while ($watch.Elapsed.TotalSeconds -lt 30) {
        $child.Process.Refresh()
        if ($child.Process.HasExited) { break }
        $port=$child.Monitor.ActivePort
        if ($port -in @(Get-TrainingPorts 'mcp')) {
            Save-TrainingProcessState $starterRoot 'mcp' $child.Process $port
            if (Test-TrainingReady $starterRoot 'mcp') { $ready=$true; break }
        }
        Start-Sleep -Milliseconds 300
    }
    if (-not $ready) {
        if ($child.Process.HasExited) {
            # Flush redirected output so the log has the server's last words.
            $child.Process.WaitForExit()
            Write-McpLog ('not_ready t={0:N1}s exited=True exit_code={1} ports_exhausted={2}' -f $watch.Elapsed.TotalSeconds, $child.Process.ExitCode, $child.Monitor.PortsExhausted)
            if ($child.Monitor.PortsExhausted) { throw 'MCP_PORTS_UNAVAILABLE' }
            if ($child.Process.ExitCode -eq 2) { throw 'MISSING_IMAP_CREDENTIALS' }
            throw 'MCP_PROCESS_EXITED'
        }
        Write-McpLog ('not_ready t={0:N1}s exited=False active_port={1}' -f $watch.Elapsed.TotalSeconds, $port)
        throw 'MCP_NOT_READY'
    }
    Write-McpLog ('READY t={0:N1}s port={1}' -f $watch.Elapsed.TotalSeconds, $port)
    Write-TrainingDiagnostic $starterRoot 'mcp' $port
    Show-McpScope
    Write-Host '[READY] MCP 준비 완료'
    if (-not $Managed) {
        Exit-TrainingLaunchLock $launchLock
        $launchLock=$null
        Write-Host ''
        Write-Host '[INFO] NAVER WORKS 로그인은 ChatGPT에서 더미 메일을 조회할 때 확인되며, 그 결과가 이 창에 표시됩니다.'
        Write-Host '이 창을 닫지 말고 유지하십시오. 이 창을 닫으면(X 또는 Ctrl+C) 이 창에서 시작한 MCP도 함께 종료됩니다.'
        Write-Host 'Tunnel 연결은 START_HERE.cmd 1번을 사용하십시오. 실행 중인 MCP를 그대로 사용합니다.'
        Write-Host '실습 종료·정리는 START_HERE.cmd 3번을 사용하십시오. MCP가 종료되면 이 창에 결과가 표시됩니다.'
        # Polling wait keeps Ctrl+C responsive; finally below stops MCP when interrupted.
        Watch-McpMailResults $child.Process $(if ($null -ne $debugLog) { $debugLog.Path } else { '' })
        $child.Process.WaitForExit()
        Write-McpLog ('mcp_exited exit_code={0}' -f $child.Process.ExitCode)
        Write-Host ''
        Write-Host '[INFO] MCP 서버가 종료됐습니다. 다시 사용하려면 부록_상시자동화 폴더의 START_MCP_ONLY.cmd를 다시 실행하십시오.'
    }
}
catch {
    $failed=$true
    # Our own failure codes are upper-case words; anything else is logged masked, never shown raw.
    $message=[string]$_.Exception.Message
    $failCode=if ($message -cmatch '^[A-Z][A-Z0-9_]+$') { $message } else { 'UNEXPECTED_ERROR' }
    $detail=if ($null -ne $debugLog) { $debugLog.Redact($message) } else { '' }
    Write-McpLog ('FAIL code={0} type={1} detail={2} at={3}' -f $failCode, $_.Exception.GetType().FullName, $detail, $_.InvocationInfo.PositionMessage)
    if (-not $Managed) { Show-TrainingFailure 'mcp' $failCode }
}
finally {
    Remove-Item Env:NW_IMAP_USER,Env:NW_IMAP_PASSWORD -ErrorAction SilentlyContinue
    $plainPassword=$null; $userName=$null
    if ($null -ne $securePassword) { $securePassword.Dispose() }
    if ($null -ne $child -and (-not $ready -or (-not $Managed -and -not $child.Process.HasExited))) {
        if (-not (Stop-TrainingRole $starterRoot 'mcp')) { Write-TrainingFail '[FAIL] MCP 정리 확인 필요. 상태 기록을 보존했습니다.' }
    }
    if ($null -ne $job) { $job.Dispose() }
    Exit-TrainingLaunchLock $launchLock
    $logPath=''
    if ($null -ne $debugLog) {
        $logPath=$debugLog.Path
        Write-McpLog ('END ready={0} failed={1} reused={2}' -f $ready, $failed, $reused)
        # A running managed MCP keeps appending its metadata-only output to the same log.
        if (-not $ready -or -not $Managed -or $reused) { $debugLog.Dispose() }
    }
}
if ($failed) {
    if ($Managed) { throw (New-TrainingFailureMessage 'mcp' $failCode $logPath) }
    Show-TrainingLogTail $logPath
    exit 1
}
