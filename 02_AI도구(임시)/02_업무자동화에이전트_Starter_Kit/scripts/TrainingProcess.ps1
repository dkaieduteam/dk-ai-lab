# Shared process identity checks. This file does not read credentials.

# [FAIL] 접두어 또는 "_RESULT: FAIL" 결과 메시지를 빨간 배경·검정 글씨로 강조 표시.
# Windows 10/11 cmd·Terminal에서 안정 지원. 호출자는 평소 Write-Host처럼 쓰면 된다.
# (TrainingProcess.ps1을 dot-source하는 모든 스크립트에서 사용 가능.)
function Write-TrainingFail {
    param([Parameter(Mandatory=$true, Position=0)][string]$Message)
    Write-Host $Message -ForegroundColor Black -BackgroundColor Red
}

function Get-TrainingPorts {
    param([ValidateSet('mcp','tunnel')][string]$Role)
    if ($Role -eq 'mcp') { return @(3000,58080,61080) }
    return @(8080,58443,61443)
}

function Enter-TrainingLaunchLock {
    param([string]$Root,[string]$Role)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $hash=[BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Root.ToLowerInvariant()))).Replace('-','') }
    finally { $sha.Dispose() }
    # Serialize both roles so MCP replacement cannot race Tunnel startup.
    $mutex=New-Object Threading.Mutex($false,("Local\AITraining-Lifecycle-{0}" -f $hash))
    try {
        try { $locked=$mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked=$true }
        if (-not $locked) { throw 'OPERATION_IN_PROGRESS' }
        return $mutex
    }
    catch { $mutex.Dispose(); throw 'OPERATION_IN_PROGRESS' }
}

function Exit-TrainingLaunchLock {
    param($Mutex)
    if ($null -ne $Mutex) { $Mutex.ReleaseMutex(); $Mutex.Dispose() }
}

function Test-TrainingPortAvailable {
    param([int]$Port)
    # A loopback bind succeeds on Windows even when another program listens on 0.0.0.0/::,
    # which later fails the owner check. Treat any existing listener as unavailable.
    if (@(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).Count -gt 0) { return $false }
    $probe = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, $Port)
    try {
        $probe.Server.ExclusiveAddressUse = $true
        $probe.Start()
        return $true
    }
    catch { return $false }
    finally { $probe.Stop() }
}

function Write-TrainingDiagnostic {
    param([string]$Root, [ValidateSet('mcp','tunnel')][string]$Role, [int]$Port)
    $dir = Join-Path $Root '.diagnostics'
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $dir "$Role-port.log"), ("ROLE={0}`r`nACTIVE_PORT={1}`r`n" -f $Role,$Port))
}

function Start-TrainingChild {
    param([string]$FilePath, [string]$Arguments, [string]$WorkingDirectory, [string]$HealthAddress='', $DebugLog=$null)
    if (-not ('TrainingOutput' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'TrainingOutput.cs') }
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$FilePath
    $info.Arguments=$Arguments
    $info.WorkingDirectory=$WorkingDirectory
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    $unrelated=if ([string]::IsNullOrEmpty($HealthAddress)) { @('CONTROL_PLANE_API_KEY','CONTROL_PLANE_TUNNEL_ID') }
        else { @('NW_IMAP_USER','NW_IMAP_PASSWORD') }
    foreach($name in $unrelated) { $info.EnvironmentVariables.Remove($name) }
    $process = New-Object Diagnostics.Process
    $process.StartInfo=$info
    $monitor = New-Object TrainingOutput($process, $HealthAddress)
    # Optional redacted copy of the child output (Tunnel diagnostics only).
    if ($null -ne $DebugLog) { $DebugLog.Attach($process) }
    if (-not $process.Start()) { throw 'SERVICE_START_FAILED' }
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    return [pscustomobject]@{ Process=$process; Monitor=$monitor }
}

function Get-TrainingProcessState {
    param([string]$Root, [ValidateSet('mcp','tunnel')][string]$Role)
    $file = Join-Path $Root ".runtime_state\$Role-process.json"
    if (-not (Test-Path -LiteralPath $file)) {
        return [pscustomobject]@{ Status='Stopped'; Process=$null; File=$file }
    }
    try {
        $state = Get-Content -Raw -Encoding UTF8 -LiteralPath $file | ConvertFrom-Json
        if ($state.role -ne $Role -or [int]$state.pid -le 0) { throw 'Invalid identity' }
        $process = Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue
        # A process that started after the recorded one cannot be the recorded process
        # (e.g. the PID was reused after a reboot), so the record is stale, not a conflict.
        if ($null -ne $process -and $state.identityVersion -ge 2) {
            try { if ($process.StartTime.ToUniversalTime().Ticks -gt [long]$state.startTimeUtcTicks) { $process=$null } } catch {}
        }
        if ($null -eq $process) {
            $orphaned=$false
            foreach ($child in @($state.children)) {
                if ($null -eq $child) { continue }
                $p=Get-Process -Id ([int]$child.pid) -ErrorAction SilentlyContinue
                if ($null -ne $p) {
                    if ($p.StartTime.ToUniversalTime().Ticks -ne [long]$child.startTimeUtcTicks -or
                        -not $p.Path.Equals([string]$child.executablePath,[StringComparison]::OrdinalIgnoreCase)) { throw 'Child identity mismatch' }
                    $orphaned=$true
                }
            }
            if ($orphaned) { return [pscustomobject]@{Status='Orphaned'; Process=$null; File=$file; Data=$state} }
            return [pscustomobject]@{ Status='Stopped'; Process=$null; File=$file; Data=$state }
        }
        $actual = [IO.Path]::GetFullPath($process.Path)
        $expected = [IO.Path]::GetFullPath([string]$state.executablePath)
        if (-not $actual.Equals($expected, [StringComparison]::OrdinalIgnoreCase)) { throw 'Path mismatch' }
        if ($state.identityVersion -ge 2) {
            if ($process.StartTime.ToUniversalTime().Ticks -ne [long]$state.startTimeUtcTicks) { throw 'PID reused' }
        }
        else {
            # Legacy state used a wall-clock timestamp, not process creation time.
            # Require this kit's exact program path in its command line.
            $details = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $process.Id) -ErrorAction Stop
            $program = if ($Role -eq 'mcp') { Join-Path $Root 'naverworks-mail-mcp\src\server.mjs' }
                else { Join-Path $Root 'tunnel-client-v0.0.15\tunnel-client-runtime-cloudflared.exe' }
            if ([string]::IsNullOrEmpty($details.CommandLine) -or
                $details.CommandLine.IndexOf($program, [StringComparison]::OrdinalIgnoreCase) -lt 0) { throw 'Legacy identity mismatch' }
        }
        if ($state.identityVersion -ge 3 -and $state.activePort -ne 0 -and
            [int]$state.activePort -notin @(Get-TrainingPorts $Role)) { throw 'Invalid port' }
        return [pscustomobject]@{ Status='Running'; Process=$process; File=$file; Data=$state }
    }
    catch {
        return [pscustomobject]@{ Status='Conflict'; Process=$null; File=$file }
    }
}

function Test-TrainingPortOwner {
    param([string]$Root, [string]$Role, [int]$Port)
    $state = Get-TrainingProcessState $Root $Role
    if ($state.Status -ne 'Running') { return $false }
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) { return $false }
    foreach ($listener in $listeners) {
        $ownerId = [int]$listener.OwningProcess
        $matched = $false
        for ($depth=0; $depth -lt 8 -and $ownerId -gt 0; $depth++) {
            if ($ownerId -eq $state.Process.Id) { $matched=$true; break }
            $child = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $ownerId) -ErrorAction SilentlyContinue
            if ($null -eq $child) { break }
            $ownerId = [int]$child.ParentProcessId
        }
        if (-not $matched) { return $false }
    }
    return $true
}

function Test-TrainingReady {
    param([string]$Root, [ValidateSet('mcp','tunnel')][string]$Role)
    $state = Get-TrainingProcessState $Root $Role
    if ($state.Status -ne 'Running') { return $false }
    $port = if ($state.Data.identityVersion -ge 3) { [int]$state.Data.activePort }
        elseif ($Role -eq 'mcp') { 3000 } else { 8080 }
    if ($port -notin @(Get-TrainingPorts $Role)) { return $false }
    if (-not (Test-TrainingPortOwner $Root $Role $port)) { return $false }
    try {
        if ($Role -eq 'mcp') {
            $health = Invoke-RestMethod ("http://127.0.0.1:{0}/healthz" -f $port) -TimeoutSec 2
            return ($health.status -eq 'ok' -and $health.readOnly -eq $true -and $health.server -eq 'naverworks-training-mail' -and
                ($state.Data.identityVersion -lt 3 -or $health.activePort -eq $port))
        }
        if ($state.Data.identityVersion -ge 3) {
            $mcp = Get-TrainingProcessState $Root 'mcp'
            if ($mcp.Status -ne 'Running' -or $state.Data.mcpPid -ne $mcp.Data.pid -or
                $state.Data.mcpStartTimeUtcTicks -ne $mcp.Data.startTimeUtcTicks -or
                $state.Data.mcpPort -ne $mcp.Data.activePort) { return $false }
        }
        $response = Invoke-WebRequest -UseBasicParsing ("http://127.0.0.1:{0}/readyz" -f $port) -TimeoutSec 2
        return ($response.StatusCode -eq 200)
    }
    catch { return $false }
}

function Test-TrainingTunnelTarget {
    param([string]$Root)
    $tunnel=Get-TrainingProcessState $Root 'tunnel'
    $mcp=Get-TrainingProcessState $Root 'mcp'
    return ($tunnel.Status -eq 'Running' -and $mcp.Status -eq 'Running' -and
        $tunnel.Data.identityVersion -ge 3 -and
        $tunnel.Data.mcpPid -eq $mcp.Data.pid -and
        $tunnel.Data.mcpStartTimeUtcTicks -eq $mcp.Data.startTimeUtcTicks -and
        $tunnel.Data.mcpPort -eq $mcp.Data.activePort)
}

function Wait-TrainingReady {
    param([string]$Root, [string]$Role, [int]$TimeoutSeconds=30)
    $watch = [Diagnostics.Stopwatch]::StartNew()
    while ($watch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        if ((Get-TrainingProcessState $Root $Role).Status -ne 'Running') { return $false }
        if (Test-TrainingReady $Root $Role) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Save-TrainingProcessState {
    param([string]$Root, [string]$Role, [Diagnostics.Process]$Process, [int]$Port=0, $McpState=$null)
    $directory = Join-Path $Root '.runtime_state'
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $children = @()
    if ($Role -eq 'tunnel') {
        $queue = New-Object 'System.Collections.Generic.Queue[int]'
        $queue.Enqueue($Process.Id)
        while ($queue.Count -gt 0) {
            $parentId = $queue.Dequeue()
            foreach ($entry in @(Get-CimInstance Win32_Process -Filter ("ParentProcessId={0}" -f $parentId) -ErrorAction Stop)) {
                $child = Get-Process -Id $entry.ProcessId -ErrorAction SilentlyContinue
                if ($null -ne $child) {
                    $children += @{pid=$child.Id; executablePath=$child.Path; startTimeUtcTicks=$child.StartTime.ToUniversalTime().Ticks}
                    $queue.Enqueue($child.Id)
                }
            }
        }
    }
    $value = [pscustomobject]@{
        identityVersion=3
        role=$Role
        pid=$Process.Id
        executablePath=$Process.Path
        startTimeUtcTicks=$Process.StartTime.ToUniversalTime().Ticks
        activePort=$Port
        mcpPid=$(if ($null -ne $McpState) {$McpState.pid} else {$null})
        mcpStartTimeUtcTicks=$(if ($null -ne $McpState) {$McpState.startTimeUtcTicks} else {$null})
        mcpPort=$(if ($null -ne $McpState) {$McpState.activePort} else {$null})
        children=$children
    }
    $destination = Join-Path $directory "$Role-process.json"
    $temporary = Join-Path $directory "$Role-process.json.tmp"
    $value | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -LiteralPath $temporary
    if (Test-Path -LiteralPath $destination) { [IO.File]::Replace($temporary,$destination,[NullString]::Value) }
    else { [IO.File]::Move($temporary,$destination) }
}

function New-TrainingFailureMessage {
    # Carries role, failure code and log path from a managed start script to the console.
    param([string]$Role, [string]$Code, [string]$LogPath)
    return ('TRAINING_FAILED|{0}|{1}|{2}' -f $Role, $Code, $LogPath)
}

function ConvertFrom-TrainingFailure {
    # Never returns the raw exception text: only our own upper-case codes pass through.
    param([string]$Message, [string]$DefaultRole='')
    $parts=([string]$Message) -split '\|', 4
    if ($parts.Count -eq 4 -and $parts[0] -eq 'TRAINING_FAILED') {
        return [pscustomobject]@{ Role=$parts[1]; Code=$parts[2]; LogPath=$parts[3] }
    }
    $code=if ([string]$Message -cmatch '^[A-Z][A-Z0-9_]+$') { [string]$Message } else { 'UNEXPECTED_ERROR' }
    return [pscustomobject]@{ Role=$DefaultRole; Code=$code; LogPath='' }
}

function Get-TrainingLatestLog {
    param([string]$Root, [ValidateSet('mcp','tunnel')][string]$Role)
    $dir=Join-Path $Root '.diagnostics'
    $latest=Get-ChildItem -LiteralPath $dir -Filter ("{0}-debug-*.log" -f $Role) -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $latest) { return '' }
    return $latest.FullName
}

function Get-TrainingFailureHint {
    param([string]$Role, [string]$Code)
    switch ($Code) {
        'OPERATION_IN_PROGRESS' { return '다른 창(START_HERE 또는 MCP 단독 실행 창)에서 시작·종료가 진행 중입니다. 그 창의 입력을 마치거나 창을 닫은 뒤 다시 시도하십시오.' }
        'STATE_CONFLICT' { return '실행 기록과 실제 프로그램이 맞지 않습니다. 강사에게 확인을 요청하십시오.' }
        'RUNNING_NOT_READY' { return '이미 실행 중이지만 응답하지 않습니다. START_HERE.cmd 3번으로 종료·정리한 뒤 다시 시작하십시오.' }
        'TUNNEL_CLEANUP_REQUIRED' { return '이전 Tunnel을 정리하지 못했습니다. START_HERE.cmd 3번으로 종료·정리하십시오.' }
        'STALE_TUNNEL_CLEANUP_REQUIRED' { return '이전 Tunnel을 정리하지 못했습니다. START_HERE.cmd 3번으로 종료·정리하십시오.' }
        'STATE_CLEANUP_REQUIRED' { return '이전 실행 기록을 정리하지 못했습니다. START_HERE.cmd 3번으로 종료·정리하십시오.' }
        'NODE_MISSING' { return 'Node.js를 찾지 못했습니다. Node.js v24 LTS 설치 여부를 확인하십시오.' }
        'NODE_VERSION' { return 'Node.js v24 LTS가 필요합니다. 설치된 버전을 강사와 확인하십시오.' }
        'DEPENDENCIES' { return 'naverworks-mail-mcp\node_modules가 없습니다. 스타터킷 압축을 다시 풀어 주십시오.' }
        'INVALID_CREDENTIAL_INPUT' { return 'ID 또는 비밀번호가 비어 있거나 줄바꿈이 포함됐습니다. 다시 실행해 입력하십시오.' }
        'MCP_PORTS_UNAVAILABLE' { return 'MCP가 사용할 수 있는 연결 후보를 다른 프로그램이 모두 사용 중입니다. 다른 실습 창·프로그램을 닫거나 강사와 확인하십시오.' }
        'MISSING_IMAP_CREDENTIALS' { return 'MCP에 계정 정보가 전달되지 않았습니다. 창을 닫고 다시 실행하십시오.' }
        'MCP_PROCESS_EXITED' { return 'MCP 서버가 시작 중에 종료됐습니다. 아래 로그를 강사와 확인하십시오.' }
        'MCP_NOT_READY' { if ($Role -eq 'tunnel') { return 'MCP가 준비되지 않아 Tunnel을 시작하지 않았습니다. MCP 상태를 먼저 확인하십시오.' } else { return 'MCP가 제한 시간 안에 준비되지 않았습니다. 아래 로그를 확인하십시오.' } }
        'MCP_NOT_READY_AFTER_START' { return 'MCP가 정상 응답하지 않습니다. 3번으로 종료·정리 후 다시 시작하십시오.' }
        'RESTART_OLD_MCP_REQUIRED' { return '이전 버전 방식으로 실행된 MCP입니다. 3번으로 종료·정리 후 다시 시작하십시오.' }
        'RUNTIME_MISSING' { return 'tunnel-client 실행 파일이 없습니다. 백신 격리 여부를 확인하고 스타터킷 압축을 다시 풀어 주십시오.' }
        'INVALID_TUNNEL_ID' { return 'Tunnel ID 형식이 3번 모두 맞지 않았습니다. OpenAI Platform의 Tunnel 화면에서 ID(tunnel_ + 소문자·숫자 32자)를 다시 복사하십시오.' }
        'INVALID_API_KEY' { return 'API Key 형식이 3번 모두 맞지 않았습니다. 발급 화면에서 sk- 로 시작하는 Key 전체를 다시 복사하십시오.' }
        'TUNNEL_AUTH_OR_NETWORK_FAILURE' { return '입력 형식은 정상입니다. 키 권한(Tunnels Read+Use)·만료·Tunnel/Key 조직 일치·네트워크를 확인하십시오.' }
        'TUNNEL_PORTS_UNAVAILABLE' { return 'Tunnel이 사용할 수 있는 연결 후보를 다른 프로그램이 모두 사용 중입니다. 강사와 확인하십시오.' }
        'TUNNEL_RUNNING_NOT_READY' { return 'Tunnel이 실행 중이지만 준비되지 않았습니다. 3번으로 정리한 뒤 다시 시작하십시오.' }
        'TUNNEL_NOT_READY_AFTER_START' { return 'Tunnel 시작 후 준비 확인에 실패했습니다. 3번으로 정리한 뒤 다시 시작하십시오.' }
        'MCP_NOT_READY_FOR_TUNNEL' { return '로컬 MCP가 응답하지 않아 Tunnel을 시작하지 않았습니다. 2번으로 상태를 확인하십시오.' }
        # Mail tool failures (classified by naverworks-mail-mcp\src\imap-errors.mjs).
        'IMAP_AUTH_FAILED' { return 'NAVER WORKS가 로그인을 거부했습니다. ID(메일 주소 전체)·비밀번호를 확인하고, 회사 설정상 IMAP 허용·외부 앱 비밀번호가 필요한지 확인하십시오. 확인 후 1회만 다시 시도하십시오.' }
        'IMAP_ACCESS_NOT_ALLOWED' { return 'IMAP 접속이 허용되지 않았거나 외부 앱 비밀번호가 필요한 계정입니다. 메일 환경설정의 IMAP 사용 여부와 보안팀 승인을 확인하십시오.' }
        'IMAP_DNS_FAILED' { return '메일 서버 주소(imap.worksmobile.com)를 찾지 못했습니다. 인터넷·DNS·프록시 설정을 확인하십시오.' }
        'IMAP_CONNECTION_FAILED' { return '메일 서버(imap.worksmobile.com:993)에 연결하지 못했습니다. 사내망 방화벽·프록시를 확인하십시오.' }
        'IMAP_TIMEOUT' { return '메일 서버 응답 시간이 초과됐습니다. 네트워크를 확인하고 잠시 후 1회만 다시 시도하십시오.' }
        'IMAP_TLS_FAILED' { return '메일 서버와 보안 연결(SSL/TLS)을 확인하지 못했습니다. 사내 SSL 검사·백신의 암호화 통신 검사·PC 시간을 확인하십시오.' }
        'TRAINING_FOLDER_NOT_FOUND' { return '로그인은 성공했지만 [AI교육_실습] 폴더가 없습니다. 웹메일에서 폴더 이름(대괄호·밑줄 포함)을 확인하십시오.' }
        'IMAP_PERMISSION_DENIED' { return '로그인은 성공했지만 [AI교육_실습] 폴더를 열 권한이 없습니다. 강사와 확인하십시오.' }
        'IMAP_RATE_LIMITED' { return '요청이 많아 메일 서버가 잠시 접속을 제한했습니다. 1~2분 뒤 다시 시도하십시오.' }
        'IMAP_SERVER_REJECTED' { return '메일 서버가 요청을 거부했습니다. 잠시 후 다시 시도하고 반복되면 강사에게 알리십시오.' }
        'MAILBOX_NOT_READ_ONLY' { return '실습 폴더를 읽기 전용으로 열지 못해 조회를 중단했습니다. 강사에게 알리십시오.' }
        'TOOL_FAILED' { return '메일 도구가 요청을 처리하지 못했습니다. 2번으로 상태를 확인하고 강사에게 알리십시오.' }
        default { return '실행 상태·실행 환경·네트워크를 강사와 확인하십시오.' }
    }
}

function Show-TrainingFailure {
    param([string]$Role, [string]$Code)
    $label=switch ($Role) { 'mcp' {'MCP 시작'} 'tunnel' {'Tunnel 연결'} 'mail' {'메일 조회'} default {'단계'} }
    Write-TrainingFail ('[FAIL] {0} 실패 (원인 코드: {1})' -f $label, $Code)
    Write-Host ('  → {0}' -f (Get-TrainingFailureHint $Role $Code))
}

function Protect-TrainingLogText {
    # Second redaction pass for screen output; log files are already redacted when written.
    param([string]$Text)
    $value=[regex]::Replace([string]$Text, 'sk-[A-Za-z0-9_\-]{6,}', 'sk-***')
    $value=[regex]::Replace($value, 'eyJ[A-Za-z0-9_\-]{10,}(\.[A-Za-z0-9_\-]+)*', 'eyJ***')
    $value=[regex]::Replace($value, '(?i)(bearer\s+)[^\s",]+', '$1***')
    $value=[regex]::Replace($value, '(?i)((api[_-]?key|authorization|token|secret|password)["'']?\s*[:=]\s*["'']?)[^\s",'']+', '$1***')
    $value=[regex]::Replace($value, 'tunnel_[A-Za-z0-9]{20,}', 'tunnel_***')
    # Local port numbers stay in .diagnostics files only; trainee screens never show them.
    $value=[regex]::Replace($value, '(?i)(127\.0\.0\.1|localhost|\[::1?\]|0\.0\.0\.0):\d{2,5}\b', '$1:****')
    $value=[regex]::Replace($value, '(?i)\b(ACTIVE_PORT|port|activePort|mcpPort|free)(["'']?\s*[:=]\s*)[\d,]+', '$1$2****')
    return $value
}

function Get-TrainingJsonField {
    # First value of a top-level-looking key in a one-line JSON log entry ('' when absent).
    param([string]$Json, [string]$Name)
    $m=[regex]::Match($Json, ('"{0}"\s*:\s*(?:"((?:\\.|[^"\\])*)"|([^,}}\s]+))' -f [regex]::Escape($Name)))
    if (-not $m.Success) { return '' }
    if (-not $m.Groups[1].Success) { return $m.Groups[2].Value }
    $value=$m.Groups[1].Value
    $value=[regex]::Replace($value, '\\u([0-9a-fA-F]{4})', { param($u) [string][char][Convert]::ToInt32($u.Groups[1].Value,16) })
    return $value.Replace('\"','"').Replace('\n',' ').Replace('\r',' ').Replace('\t',' ').Replace('\\','\')
}

function ConvertTo-TrainingLogLine {
    # 'yyyy-MM-dd HH:mm:ss.fff [SRC] text' -> 'HH:mm:ss SRC text'; runtime JSON -> 'LEVEL msg | error'.
    param([string]$Line)
    $m=[regex]::Match($Line, '^\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\.\d{3} \[([A-Z]+)\] (.*)$')
    if (-not $m.Success) { return $null }
    $time=$m.Groups[1].Value; $source=$m.Groups[2].Value; $text=$m.Groups[3].Value
    $level=''
    if ($text.StartsWith('{')) {
        # Regex instead of ConvertFrom-Json: the runtime repeats keys (tunnel_id), which PS 5.1 rejects.
        $level=Get-TrainingJsonField $text 'level'
        $items=@()
        if ($level) { $items+=$level.ToUpperInvariant() }
        $msg=Get-TrainingJsonField $text 'msg'
        $tool=Get-TrainingJsonField $text 'tool'
        $route=Get-TrainingJsonField $text 'route'
        if ($msg) { $items+=$msg }
        elseif ($tool) { $items+=('tool={0} result={1}' -f $tool, (Get-TrainingJsonField $text 'result')) }
        elseif ($route) { $items+=('route={0} result={1}' -f $route, (Get-TrainingJsonField $text 'result')) }
        $extra=@()
        foreach ($name in @('error','code','errorType','status_code','upstream_status','failure_source')) {
            $v=Get-TrainingJsonField $text $name
            if ($v) { $extra+=$(if ($name -eq 'error') { $v } else { '{0}={1}' -f $name,$v }) }
        }
        if ($extra.Count -gt 0) { $items+=('| ' + ($extra -join ' ')) }
        if ($items.Count -gt 0) { $text=$items -join ' ' }
    }
    $text=Protect-TrainingLogText $text
    if ($text.Length -gt 220) { $text=$text.Substring(0,217) + '...' }
    return [pscustomobject]@{ Source=$source; Level=$level.ToUpperInvariant(); Text=('{0} {1} {2}' -f $time,$source,$text) }
}

function Get-TrainingLogTail {
    # Last meaningful lines: runtime WARN/ERROR, stderr, and our own failure steps.
    param([string]$Path, [int]$MaxLines=15)
    if ([string]::IsNullOrEmpty($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @() }
    $lines=@()
    try {
        $stream=New-Object IO.FileStream($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        try {
            $reader=New-Object IO.StreamReader($stream, (New-Object Text.UTF8Encoding($false)))
            $lines=$reader.ReadToEnd() -split "`r?`n"
        }
        finally { $stream.Dispose() }
    } catch { return @() }
    $all=@(); $picked=@()
    foreach ($raw in $lines) {
        if ([string]::IsNullOrWhiteSpace($raw)) { continue }
        $entry=ConvertTo-TrainingLogLine $raw
        if ($null -eq $entry) { continue }
        $all+=$entry.Text
        $important=$false
        # 'OAuth discovery failed' also appears in every successful run (the MCP does not advertise OAuth).
        if ($raw -match '"msg":"OAuth discovery failed"') { $important=$false }
        elseif ($entry.Level -in @('ERROR','WARN','WARNING','FATAL','PANIC')) { $important=$true }
        elseif ($entry.Source -eq 'ERR') { $important=$true }
        elseif ($entry.Source -eq 'STEP' -and $raw -cmatch 'FAIL code=|_rejected |not_ready |available=NO|control_plane_check=FAIL|job_assign=(False|FAIL)') { $important=$true }
        elseif ($entry.Source -eq 'OUT' -and $raw -match '(?i)error|fail|denied|unauthori|invalid|EADDRINUSE|UNAVAILABLE') { $important=$true }
        if ($important) { $picked+=$entry.Text }
    }
    if ($picked.Count -eq 0) { $picked=$all }
    # Collapse consecutive repeats (e.g. the same 401 on every poll retry): 'text (xN)'.
    $collapsed=@(); $previous=$null; $repeat=0
    foreach ($line in $picked) {
        $body=$line.Substring([Math]::Min(9, $line.Length))
        if ($null -ne $previous -and $body -eq $previous) { $repeat++; continue }
        if ($repeat -gt 0) { $collapsed[$collapsed.Count - 1]+=(' (x{0})' -f ($repeat + 1)) }
        $collapsed+=$line; $previous=$body; $repeat=0
    }
    if ($repeat -gt 0) { $collapsed[$collapsed.Count - 1]+=(' (x{0})' -f ($repeat + 1)) }
    $picked=$collapsed
    if ($picked.Count -gt $MaxLines) { $picked=$picked[($picked.Count - $MaxLines)..($picked.Count - 1)] }
    return $picked
}

function Show-TrainingLogTail {
    param([string]$Path, [int]$MaxLines=15)
    if ([string]::IsNullOrEmpty($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Write-Host '[INFO] 이 단계의 진단 로그가 없습니다.'
        return
    }
    $tail=@(Get-TrainingLogTail $Path $MaxLines)
    Write-Host ('---- 진단 로그 핵심 {0}줄 (비밀값은 가려서 기록) ----' -f $tail.Count)
    foreach ($line in $tail) { Write-Host ('  ' + $line) }
    Write-Host '------------------------------------------------------'
    $joined=$tail -join "`n"
    if ($joined -match '(?i)invalid_api_key|incorrect api key|\b401\b') { Write-Host '[해석] 401/invalid_api_key: API Key가 틀렸거나 Revoke·만료된 Key입니다. 새 Key를 발급해 다시 입력하십시오.' }
    elseif ($joined -match '(?i)\b403\b|forbidden|permission') { Write-Host '[해석] 403/권한 부족: Key 권한(Tunnels Read+Use)과 Tunnel·Key의 조직·프로젝트 일치를 확인하십시오.' }
    elseif ($joined -match '(?i)\b404\b|not[ _]found') { Write-Host '[해석] 404/찾을 수 없음: Tunnel ID가 Key와 같은 조직의 Tunnel인지 확인하십시오.' }
    elseif ($joined -match '(?i)MCP_PORTS_UNAVAILABLE|EADDRINUSE|address already in use') { Write-Host '[해석] 연결 포트를 다른 프로그램이 사용 중입니다.' }
    Write-Host ('[INFO] 진단 로그 파일: {0}' -f $Path)
    Write-Host '[INFO] 강사에게 보여 줄 때는 위 화면이나 로그 파일을 사용하십시오. 비밀번호·Key는 채팅에 붙이지 마십시오.'
}

function Read-TrainingLogText {
    # Shared read of a log that the running MCP may still be appending to ('' when unavailable).
    param([string]$Path, [long]$Offset=0)
    if ([string]::IsNullOrEmpty($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) { return '' }
    try {
        $stream=New-Object IO.FileStream($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        try {
            if ($Offset -gt 0 -and $Offset -le $stream.Length) { [void]$stream.Seek($Offset, [IO.SeekOrigin]::Begin) }
            return (New-Object IO.StreamReader($stream, (New-Object Text.UTF8Encoding($false)))).ReadToEnd()
        }
        finally { $stream.Dispose() }
    } catch { return '' }
}

function Get-TrainingMcpLogForProcess {
    # The debug log of the MCP process that is running now (matched by its recorded node PID).
    param([string]$Root, [int]$ProcessId)
    $dir=Join-Path $Root '.diagnostics'
    $logs=@(Get-ChildItem -LiteralPath $dir -Filter 'mcp-debug-*.log' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 20)
    foreach ($log in $logs) {
        if ((Read-TrainingLogText $log.FullName) -match ('(?m)\[STEP\] node_pid={0}\r?$' -f $ProcessId)) { return $log.FullName }
    }
    return ''
}

function Get-TrainingMailResults {
    # Mail tool results from the MCP metadata log: tool, result and our own code only.
    param([string]$Text)
    $results=@()
    foreach ($line in ([string]$Text -split "`r?`n")) {
        if ($line -notmatch '\[OUT\] \{.*"tool":"(search_training_mails|read_training_mail)"') { continue }
        $json=$line.Substring($line.IndexOf('{'))
        $code=Get-TrainingJsonField $json 'code'
        $results+=[pscustomobject]@{
            Tool=Get-TrainingJsonField $json 'tool'
            Result=Get-TrainingJsonField $json 'result'
            Code=$(if ($code -cmatch '^[A-Z][A-Z0-9_]{1,40}$') { $code } else { '' })
        }
    }
    return $results
}

function Show-TrainingMailResult {
    # One line for the latest mail tool call (menu 2 / MCP-only window). Silent before the first call.
    param($Result)
    if ($null -eq $Result) { return }
    if ($Result.Result -eq 'success') {
        Write-Host '[OK] 최근 메일 조회 성공 (NAVER WORKS 인증 확인됨)'
        return
    }
    # Scope refusals are the safety limits working, not a connection failure.
    if ($Result.Code -in @('UID_OUT_OF_SCOPE','TITLE_CATEGORY_INVALID','ATTACHMENTS_NOT_ALLOWED','TRAINING_MARKER_MISSING','MESSAGE_TOO_LARGE')) {
        Write-Host ('[INFO] 최근 메일 요청이 안전 범위에서 거부됨 (원인 코드: {0}) — 안전장치 정상 작동' -f $Result.Code)
        return
    }
    $code=if ($Result.Code) { $Result.Code } else { 'TOOL_FAILED' }
    Show-TrainingFailure 'mail' $code
}

function Get-TrainingAutostartShortcutPath {
    # Current user's Startup folder only: no admin rights, no scheduled task.
    return (Join-Path ([Environment]::GetFolderPath('Startup')) 'AITraining-MCP-Only.lnk')
}

function Stop-TrainingRole {
    param([string]$Root, [ValidateSet('mcp','tunnel')][string]$Role)
    $lock=Enter-TrainingLaunchLock $Root $Role
    try { return Stop-TrainingRoleCore $Root $Role }
    finally { Exit-TrainingLaunchLock $lock }
}

function Stop-TrainingRoleCore {
    param([string]$Root, [ValidateSet('mcp','tunnel')][string]$Role)
    $state = Get-TrainingProcessState $Root $Role
    if ($state.Status -eq 'Conflict') { return $false }
    if ($state.Status -eq 'Orphaned') {
        foreach ($identity in @($state.Data.children)) {
            $p=Get-Process -Id ([int]$identity.pid) -ErrorAction SilentlyContinue
            if ($null -eq $p) { continue }
            if ($p.StartTime.ToUniversalTime().Ticks -ne [long]$identity.startTimeUtcTicks -or
                -not $p.Path.Equals([string]$identity.executablePath,[StringComparison]::OrdinalIgnoreCase)) { return $false }
            & taskkill.exe /PID $p.Id /T /F 2>$null | Out-Null
        }
        if ((Get-TrainingProcessState $Root $Role).Status -ne 'Stopped') { return $false }
    }
    if ($state.Status -eq 'Running') {
        Save-TrainingProcessState $Root $Role $state.Process ([int]$state.Data.activePort)
        $saved = Get-Content -Raw -Encoding UTF8 $state.File | ConvertFrom-Json
        if ((Get-TrainingProcessState $Root $Role).Status -ne 'Running') { return $false }
        & taskkill.exe /PID $state.Process.Id /T /F 2>$null | Out-Null
        Start-Sleep -Milliseconds 300
        foreach ($identity in @($saved) + @($saved.children)) {
            if ($null -eq $identity) { continue }
            $p = Get-Process -Id ([int]$identity.pid) -ErrorAction SilentlyContinue
            if ($null -ne $p -and $p.StartTime.ToUniversalTime().Ticks -eq [long]$identity.startTimeUtcTicks) { return $false }
        }
    }
    Remove-Item -LiteralPath $state.File -Force -ErrorAction SilentlyContinue
    return (-not (Test-Path -LiteralPath $state.File))
}
