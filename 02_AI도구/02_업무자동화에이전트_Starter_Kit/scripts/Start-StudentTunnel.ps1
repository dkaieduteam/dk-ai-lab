[CmdletBinding()]
param([switch]$Managed)
# Screen wording follows the course material (교안 Chap 2 ✅2). Local ports are never shown on screen.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$starterRoot=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'TrainingProcess.ps1')
$runtimeFolder=Join-Path $starterRoot 'tunnel-client-v0.0.15'
$runtimePath=Join-Path $runtimeFolder 'tunnel-client-runtime-cloudflared.exe'
$secureTunnelId=$null; $secureApiKey=$null; $child=$null
$ready=$false; $failed=$false; $failCode=$null; $launchLock=$null
$script:tunnelInputCancelled=$false

# Detailed diagnostic log (.diagnostics\tunnel-debug-*.log). Secrets are masked before writing.
$debugLog=$null
try {
    if (-not ('TrainingDebugLog' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'TrainingDebugLog.cs') }
    $debugLog=New-Object TrainingDebugLog((Join-Path $starterRoot ('.diagnostics\tunnel-debug-{0:yyyyMMdd-HHmmss}.log' -f (Get-Date))))
}
catch { Write-Host '[INFO] 진단 로그 파일을 만들지 못했습니다. 실행은 계속합니다.' }

function Write-TunnelLog {
    param([string]$Message)
    if ($null -ne $script:debugLog) { $script:debugLog.Write('STEP', $Message) }
}

function Get-TunnelInputShape {
    # Describes the shape of an input without writing its value.
    param([string]$Value, [string]$Kind)
    if ($null -eq $Value) { return ('{0}: null' -f $Kind) }
    $parts=@(('len={0}' -f $Value.Length), ('trimmed_len={0}' -f $Value.Trim().Length))
    if ($Value -ne $Value.Trim()) { $parts+='leading_or_trailing_whitespace=YES' }
    if ($Value -match '[\r\n]') { $parts+='line_break=YES' }
    if ($Value.Trim() -match '\s') { $parts+='inner_whitespace=YES' }
    if ($Value -match '["''`]') { $parts+='quote_char=YES' }
    if ($Kind -eq 'TUNNEL_ID') {
        $parts+=('starts_with_tunnel_={0}' -f $(if ($Value.StartsWith('tunnel_', [StringComparison]::Ordinal)) {'YES'} else {'NO'}))
        $parts+=('tunnel_prefix_count={0}' -f ([regex]::Matches($Value, '(?i)tunnel_')).Count)
        $invalid=@($Value.ToCharArray() | Where-Object { $_ -notmatch '[A-Za-z0-9_-]' } | Sort-Object -Unique |
            ForEach-Object { 'U+{0:X4}' -f [int]$_ })
        if ($invalid.Count -gt 0) { $parts+=('invalid_chars={0}' -f ($invalid -join ',')) }
        if ($Value.Trim().StartsWith('sk-')) { $parts+='HINT=API_KEY_PASTED_INTO_TUNNEL_ID' }
        $parts+=('format_check={0}' -f $(if ($Value -match '^tunnel_[A-Za-z0-9_-]+$') {'PASS'} else {'FAIL'}))
        # tunnel-client v0.0.15 itself accepts only tunnel_ + 32 lowercase letters/digits.
        $parts+=('runtime_format_check={0}' -f $(if ($Value -cmatch '^tunnel_[a-z0-9]{32}$') {'PASS'} else {'FAIL'}))
        $parts+=('masked={0}' -f [TrainingDebugLog]::Mask($Value))
    }
    else {
        $prefix=switch -Regex ($Value.Trim()) {
            '^sk-proj-' {'sk-proj-'} '^sk-svcacct-' {'sk-svcacct-'} '^sk-admin-' {'sk-admin-'}
            '^sk-' {'sk-'} '^tunnel_' {'tunnel_ (HINT=TUNNEL_ID_PASTED_INTO_API_KEY)'} default {'other'}
        }
        $parts+=('prefix={0}' -f $prefix)
        $parts+=('format_check={0}' -f $(if (-not [string]::IsNullOrWhiteSpace($Value) -and $Value -notmatch '[\r\n]') {'PASS'} else {'FAIL'}))
    }
    return ('{0}: {1}' -f $Kind, ($parts -join ' '))
}

function Get-TunnelIdProblem {
    # tunnel-client v0.0.15 accepts only tunnel_ + 32 lowercase letters/digits (39 characters).
    param([string]$Value)
    if ([string]::IsNullOrEmpty($Value)) { return '아무것도 입력되지 않았습니다.' }
    if ($Value.StartsWith('sk-')) { return 'API Key가 입력된 것 같습니다. 이 칸에는 Tunnel ID를 넣으십시오.' }
    if (([regex]::Matches($Value, '(?i)tunnel_')).Count -gt 1) { return '두 번 붙여넣은 것 같습니다. 한 번만 붙여넣으십시오.' }
    if (-not $Value.StartsWith('tunnel_', [StringComparison]::Ordinal)) { return 'tunnel_ 로 시작해야 합니다. Tunnel 이름이 아니라 ID 값을 복사하십시오.' }
    if ($Value -match '\s') { return '중간에 공백이나 줄바꿈이 있습니다.' }
    if ($Value -cmatch '[A-Z]') { return '대문자가 섞여 있습니다. Tunnel ID는 소문자와 숫자로만 됩니다.' }
    if ($Value -cnotmatch '^tunnel_[a-z0-9]*$') { return 'tunnel_ 뒤에 소문자·숫자가 아닌 문자가 있습니다.' }
    if ($Value.Length -ne 39) { return ('길이가 맞지 않습니다(입력 {0}자, 정상 39자). 끝까지 복사됐는지 확인하십시오.' -f $Value.Length) }
    return $null
}

function Get-ApiKeyProblem {
    param([string]$Value)
    if ([string]::IsNullOrEmpty($Value)) { return '아무것도 입력되지 않았습니다.' }
    if ($Value.StartsWith('tunnel_')) { return 'Tunnel ID가 입력된 것 같습니다. 이 칸에는 API Key를 넣으십시오.' }
    if ($Value -match '\s') { return '중간에 공백이나 줄바꿈이 있습니다.' }
    if (-not $Value.StartsWith('sk-', [StringComparison]::Ordinal)) { return 'OpenAI API Key는 sk- 로 시작합니다.' }
    if ($Value.Length -lt 20) { return ('너무 짧습니다(입력 {0}자). 끝까지 복사됐는지 확인하십시오.' -f $Value.Length) }
    return $null
}

function Read-TunnelSecret {
    # Hidden input with up to 3 tries; strips surrounding spaces/quotes that copy-paste often adds.
    # -AllowCancel: an empty first answer means "not ready yet" and returns to the menu.
    param([string]$Prompt, [string]$Kind, [scriptblock]$GetProblem, [switch]$AllowCancel)
    for ($attempt=1; $attempt -le 3; $attempt++) {
        $secure=Read-Host $Prompt -AsSecureString
        $raw=([Net.NetworkCredential]::new('', $secure)).Password
        $secure.Dispose()
        $value=$raw.Trim().Trim([char[]]@('"', "'")).Trim()
        if ($AllowCancel -and $attempt -eq 1 -and $value.Length -eq 0) {
            Write-TunnelLog ('{0} input_cancelled attempt=1' -f $Kind)
            $script:tunnelInputCancelled=$true
            return $null
        }
        if ($null -ne $script:debugLog) { $script:debugLog.AddSecret($raw); $script:debugLog.AddSecret($value) }
        Write-TunnelLog ('attempt={0} {1}' -f $attempt, (Get-TunnelInputShape $raw $Kind))
        $problem=& $GetProblem $value
        $raw=$null
        if ($null -eq $problem) {
            # Only the Tunnel ID line is shown (교안 result example); the key check is logged.
            if ($Kind -eq 'TUNNEL_ID') { Write-Host '[PASS] tunnel_id 형식 확인' }
            Write-TunnelLog ('{0}_format=PASS attempt={1}' -f $Kind, $attempt)
            return $value
        }
        $value=$null
        Write-TunnelLog ('{0}_rejected attempt={1} reason={2}' -f $Kind, $attempt, $problem)
        Write-Host ('[다시 입력] {0}' -f $problem)
        if ($attempt -lt 3) { Write-Host ('  남은 기회 {0}번' -f (3 - $attempt)) }
    }
    return $null
}

function Get-TunnelHealthText {
    # Reads a health endpoint, including the body of non-200 answers.
    param([string]$Url)
    try {
        $response=Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        # Without a text Content-Type, PS 5.1 returns the body as bytes; decode instead of printing System.Byte[].
        $content=if ($response.Content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($response.Content) } else { [string]$response.Content }
        return ('{0} {1}' -f $response.StatusCode, $content)
    }
    catch {
        $failure=$_.Exception.Response
        if ($null -eq $failure) { return ('NO_RESPONSE {0}' -f $_.Exception.GetType().Name) }
        $body=''
        try { $reader=New-Object IO.StreamReader($failure.GetResponseStream()); $body=$reader.ReadToEnd(); $reader.Dispose() } catch {}
        return ('{0} {1}' -f [int]$failure.StatusCode, $body)
    }
}

function Read-TunnelLogSince {
    # Text appended to the redacted debug log after the given offset ('' when unavailable).
    param([long]$Offset)
    if ($null -eq $script:debugLog) { return '' }
    try {
        $stream=New-Object IO.FileStream($script:debugLog.Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        try {
            if ($Offset -gt 0 -and $Offset -le $stream.Length) { [void]$stream.Seek($Offset, [IO.SeekOrigin]::Begin) }
            return (New-Object IO.StreamReader($stream, (New-Object Text.UTF8Encoding($false)))).ReadToEnd()
        }
        finally { $stream.Dispose() }
    } catch { return '' }
}

function Wait-TunnelControlPlane {
    # tunnel-client /readyz answers 200 even while the control plane rejects the key (401),
    # so readiness is confirmed only after the control plane accepted the Tunnel ID and key.
    param([string]$HealthAddress, [long]$LogOffset, [Diagnostics.Process]$Process, [int]$TimeoutSeconds=20)
    $watch=[Diagnostics.Stopwatch]::StartNew()
    $state='unknown'; $httpStatus=''
    while ($watch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $Process.Refresh()
        if ($Process.HasExited) { return 'FAIL runtime_exited' }
        $logText=Read-TunnelLogSince $LogOffset
        if ($logText -match '"msg":"tunnel metadata fetched"') { return 'OK metadata_fetched' }
        $health=Get-TunnelHealthText ("http://{0}/health?details=true" -f $HealthAddress)
        $m=[regex]::Match($health, '"control-plane":\{"status":"([A-Za-z_]+)"')
        if ($m.Success) { $state=$m.Groups[1].Value }
        $d=[regex]::Match($health, '"control-plane":\{[^{}]*"details":\{([^{}]*)\}')
        $h=if ($d.Success) { [regex]::Match($d.Groups[1].Value, '"http_status":(\d+)') } else { [regex]::Match('', 'x') }
        if ($h.Success) { $httpStatus=$h.Groups[1].Value }
        if ($state -eq 'ok') { return 'OK control_plane_ok' }
        if ($httpStatus -in @('401','403','404') -or $logText -match '"msg":"tunnel metadata fetch failed"') {
            return ('FAIL control_plane={0} http_status={1}' -f $state, $httpStatus)
        }
        Start-Sleep -Milliseconds 500
    }
    if ($state -eq 'degraded') { return ('FAIL control_plane=degraded_timeout http_status={0}' -f $httpStatus) }
    return ('OK unconfirmed control_plane={0}' -f $state)
}

$kitVersion=(Get-Content -LiteralPath (Join-Path $starterRoot 'VERSION.txt') -ErrorAction SilentlyContinue | Select-String '^STARTER_KIT_VERSION=') -join ''
Write-TunnelLog ('START kit={0} ps={1} os={2} managed={3}' -f $kitVersion, $PSVersionTable.PSVersion, [Environment]::OSVersion.VersionString, [bool]$Managed)
try {
    $launchLock=Enter-TrainingLaunchLock $starterRoot 'tunnel'
    $previous=Get-TrainingProcessState $starterRoot 'tunnel'
    Write-TunnelLog ('previous_tunnel_state={0}' -f $previous.Status)
    if ($previous.Status -eq 'Conflict') { throw 'STATE_CONFLICT' }
    if ($previous.Status -eq 'Running') {
        if (-not (Test-TrainingTunnelTarget $starterRoot)) {
            if (-not (Stop-TrainingRole $starterRoot 'tunnel')) { throw 'STALE_TUNNEL_CLEANUP_REQUIRED' }
        }
        elseif (Wait-TrainingReady $starterRoot 'tunnel' 10) {
            Write-Host '[PASS] Tunnel 상태 확인 (이미 실행 중 — 중복 실행하지 않았습니다)'
            if (-not $Managed) { Write-Host '[READY] 요청 대기 중' }
            return
        }
        else { throw 'RUNNING_NOT_READY' }
    }
    if (-not (Wait-TrainingReady $starterRoot 'mcp' 30)) { throw 'MCP_NOT_READY' }
    $mcp=(Get-TrainingProcessState $starterRoot 'mcp').Data
    Write-TunnelLog ('mcp_ready=YES pid={0} port={1} identityVersion={2}' -f $mcp.pid, $mcp.activePort, $mcp.identityVersion)
    if ($mcp.identityVersion -lt 3) { throw 'RESTART_OLD_MCP_REQUIRED' }
    if (-not (Stop-TrainingRole $starterRoot 'tunnel')) { throw 'STATE_CLEANUP_REQUIRED' }
    if (-not (Test-Path -LiteralPath $runtimePath)) { throw 'RUNTIME_MISSING' }
    # v2: Load TUNNEL_ID/API_KEY from .env (replaces interactive hidden input)
    $envFile=Join-Path $starterRoot '.env'
    if (-not (Test-Path -LiteralPath $envFile)) {
        Write-TunnelLog 'env_missing'
        throw 'ENV_FILE_MISSING'
    }
    $envVars=@{}
    Get-Content -LiteralPath $envFile -Encoding UTF8 | ForEach-Object {
        $line=$_.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { return }
        $eq=$line.IndexOf('=')
        if ($eq -le 0) { return }
        $key=$line.Substring(0, $eq).Trim()
        $value=$line.Substring($eq + 1).Trim()
        if ($value.StartsWith('"') -and $value.EndsWith('"')) {
            $value=$value.Substring(1, $value.Length - 2)
        }
        $envVars[$key]=$value
    }
    $plainTunnelId=$envVars['TUNNEL_ID']
    $plainApiKey=$envVars['API_KEY']
    if ($null -ne $debugLog) {
        if ($plainTunnelId) { $debugLog.AddSecret($plainTunnelId) }
        if ($plainApiKey) { $debugLog.AddSecret($plainApiKey) }
    }
    $tunnelIdProblem=Get-TunnelIdProblem $plainTunnelId
    if ($tunnelIdProblem) {
        Write-TunnelLog ('tunnel_id_invalid: {0}' -f $tunnelIdProblem)
        Write-TrainingFail ('[FAIL] .env의 TUNNEL_ID 값 문제 — {0}' -f $tunnelIdProblem)
        throw 'INVALID_TUNNEL_ID'
    }
    $apiKeyProblem=Get-ApiKeyProblem $plainApiKey
    if ($apiKeyProblem) {
        Write-TunnelLog ('api_key_invalid: {0}' -f $apiKeyProblem)
        Write-TrainingFail ('[FAIL] .env의 API_KEY 값 문제 — {0}' -f $apiKeyProblem)
        throw 'INVALID_API_KEY'
    }
    Write-Host '[PASS] tunnel_id 형식 확인 (.env)'
    Write-TunnelLog 'env_load_format=PASS'
    # Re-confirm the local MCP right before connecting (the inputs may have taken a while).
    if (-not (Test-TrainingReady $starterRoot 'mcp')) { throw 'MCP_NOT_READY_FOR_TUNNEL' }
    $mcp=(Get-TrainingProcessState $starterRoot 'mcp').Data
    Write-Host '[PASS] 로컬 MCP 연결 확인'
    $mcpUrl='http://127.0.0.1:{0}/mcp' -f $mcp.activePort
    # info by default; set AITRAINING_TUNNEL_LOG_LEVEL=debug before START_HERE.cmd for more runtime detail.
    $logLevel=if ($env:AITRAINING_TUNNEL_LOG_LEVEL -in @('debug','info','warn')) { $env:AITRAINING_TUNNEL_LOG_LEVEL } else { 'info' }
    foreach ($port in @(Get-TrainingPorts 'tunnel')) {
        if (-not (Test-TrainingPortAvailable $port)) { Write-TunnelLog ('port={0} available=NO (skip)' -f $port); continue }
        $healthAddress='127.0.0.1:{0}' -f $port
        $env:CONTROL_PLANE_TUNNEL_ID=$plainTunnelId
        $env:CONTROL_PLANE_API_KEY=$plainApiKey
        $arguments='run --mcp.server-url url={0},channel=main --health.listen-addr {1} --health.show-details --log.format json --log.level {2}' -f $mcpUrl,$healthAddress,$logLevel
        $logOffset=if ($null -ne $debugLog) { (Get-Item -LiteralPath $debugLog.Path).Length } else { 0 }
        Write-TunnelLog ('launch runtime="{0}" args="{1}"' -f $runtimePath, $arguments)
        $child=Start-TrainingChild $runtimePath $arguments $runtimeFolder $healthAddress $debugLog
        Write-TunnelLog ('runtime_pid={0}' -f $child.Process.Id)
        # Keep identity immediately, but publish the active port only after readiness.
        Save-TrainingProcessState $starterRoot 'tunnel' $child.Process 0 $mcp
        Remove-Item Env:CONTROL_PLANE_TUNNEL_ID,Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
        $watch=[Diagnostics.Stopwatch]::StartNew()
        $nextProbeLog=0
        while ($watch.Elapsed.TotalSeconds -lt 60) {
            $child.Process.Refresh()
            if ($child.Process.HasExited -or $child.Monitor.BindFailed) { break }
            $portOwned=Test-TrainingPortOwner $starterRoot 'tunnel' $port
            if ($portOwned) {
                $readyz=$false
                try {
                    $response=Invoke-WebRequest -UseBasicParsing -Uri ("http://{0}/readyz" -f $healthAddress) -TimeoutSec 2
                    if ($response.StatusCode -eq 200) { $readyz=$true }
                } catch {}
                if ($readyz) {
                    Write-TunnelLog ('readyz=200 t={0:N1}s; confirming control plane' -f $watch.Elapsed.TotalSeconds)
                    $controlPlane=Wait-TunnelControlPlane $healthAddress $logOffset $child.Process
                    Write-TunnelLog ('control_plane_check={0}' -f $controlPlane)
                    if ($controlPlane.StartsWith('OK')) { $ready=$true }
                    break
                }
            }
            if ($watch.Elapsed.TotalSeconds -ge $nextProbeLog) {
                $readyText=if ($portOwned) { Get-TunnelHealthText ("http://{0}/readyz" -f $healthAddress) } else { 'health port not listening yet' }
                Write-TunnelLog ('wait t={0:N0}s port_owned={1} readyz={2}' -f $watch.Elapsed.TotalSeconds, $portOwned, $readyText)
                $nextProbeLog+=5
            }
            Start-Sleep -Milliseconds 300
        }
        if ($ready) {
            Write-TunnelLog ('READY t={0:N1}s port={1}' -f $watch.Elapsed.TotalSeconds, $port)
            Write-TunnelLog ('health_details={0}' -f (Get-TunnelHealthText ("http://{0}/health?details=true" -f $healthAddress)))
            Save-TrainingProcessState $starterRoot 'tunnel' $child.Process $port $mcp
            Write-TrainingDiagnostic $starterRoot 'tunnel' $port
            break
        }
        if (-not $child.Process.HasExited) {
            Write-TunnelLog ('health_details_at_failure={0}' -f (Get-TunnelHealthText ("http://{0}/health?details=true" -f $healthAddress)))
        }
        # Flush redirected output before checking the classification on exit.
        if ($child.Process.HasExited) { $child.Process.WaitForExit() }
        Write-TunnelLog ('not_ready t={0:N1}s exited={1} exit_code={2} bind_failed={3}' -f $watch.Elapsed.TotalSeconds, $child.Process.HasExited,
            $(if ($child.Process.HasExited) { $child.Process.ExitCode } else { '-' }), $child.Monitor.BindFailed)
        $bindingFailure=$child.Monitor.BindFailed
        if (-not (Stop-TrainingRole $starterRoot 'tunnel')) { throw 'TUNNEL_CLEANUP_REQUIRED' }
        $child=$null
        if (-not $bindingFailure) { throw 'TUNNEL_AUTH_OR_NETWORK_FAILURE' }
    }
    if (-not $ready) { throw 'TUNNEL_PORTS_UNAVAILABLE' }
    $plainApiKey=$null; $plainTunnelId=$null
    Write-Host '[PASS] Tunnel 상태 확인'
    if (-not $Managed) {
        Exit-TrainingLaunchLock $launchLock
        $launchLock=$null
        Write-Host '[READY] 요청 대기 중'
        Write-Host '이 창을 유지하십시오. 종료는 START_HERE.cmd 3번을 사용하십시오.'
        $child.Process.WaitForExit()
    }
}
catch {
    $failed=$true
    # Our own failure codes are upper-case words; anything else is logged masked, never shown raw.
    $message=[string]$_.Exception.Message
    $failCode=if ($message -cmatch '^[A-Z_]+$') { $message } else { 'UNEXPECTED_ERROR' }
    $detail=if ($null -ne $debugLog) { $debugLog.Redact($message) } else { '' }
    Write-TunnelLog ('FAIL code={0} type={1} detail={2} at={3}' -f $failCode, $_.Exception.GetType().FullName, $detail, $_.InvocationInfo.PositionMessage)
    if ($failCode -eq 'TUNNEL_INPUT_CANCELLED' -and -not $Managed) {
        # Not a failure: the learner chose to come back after preparing the Tunnel.
        $failed=$false
        Write-Host '[INFO] Tunnel 입력을 취소했습니다. 준비되면 다시 실행하십시오.'
    }
    # Managed: START_HERE shows code + log tail. Standalone: shown below after cleanup.
    elseif (-not $Managed) { Show-TrainingFailure 'tunnel' $failCode }
}

finally {
    Remove-Item Env:CONTROL_PLANE_TUNNEL_ID,Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
    $plainApiKey=$null; $plainTunnelId=$null
    if ($null -ne $secureApiKey) { $secureApiKey.Dispose() }
    if ($null -ne $secureTunnelId) { $secureTunnelId.Dispose() }
    if ($null -ne $child -and (-not $ready -or (-not $Managed -and -not $child.Process.HasExited))) {
        if (-not (Stop-TrainingRole $starterRoot 'tunnel')) { Write-TrainingFail '[FAIL] Tunnel 정리 확인 필요. 상태 기록을 보존했습니다.' }
    }
    Exit-TrainingLaunchLock $launchLock
    $logPath=''
    if ($null -ne $debugLog) {
        $logPath=$debugLog.Path
        Write-TunnelLog ('END ready={0} failed={1}' -f $ready, $failed)
        # A running managed Tunnel keeps appending its output to the same log.
        if (-not $ready -or -not $Managed) { $debugLog.Dispose() }
    }
}
if ($failed) {
    if ($Managed) { throw (New-TrainingFailureMessage 'tunnel' $failCode $logPath) }
    Show-TrainingLogTail $logPath
    exit 1
}
