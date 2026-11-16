[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$starterRoot=Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'TrainingProcess.ps1')
$failureCount=0
$locks=@()

# -------------------------------------------------------------------
# 포트 해제 검증 유틸 — PID 종료는 "요청"일 뿐, 실제 해제까지 비동기.
# 포트 바인딩 가능 여부를 종료 완료 기준으로 사용한다.
# -------------------------------------------------------------------
function Test-PortFree {
    param([int]$Port)
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch { return $false }
}

function Get-BusyPorts {
    param([int[]]$Ports)
    return @($Ports | Where-Object { -not (Test-PortFree $_) })
}

function Wait-PortsReleased {
    param([int[]]$Ports, [int]$TimeoutSeconds = 15)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        if ((Get-BusyPorts $Ports).Count -eq 0) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Stop-ProcessesByPort {
    # 지정 포트를 Listen 중인 PID만 강제 종료 — 프로세스 이름 기반이 아니라
    # 포트 소유 PID 기준이므로 다른 업무용 node.exe 등을 건드리지 않는다.
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        try {
            $conns = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
            foreach ($c in $conns) {
                if ($c.OwningProcess -and $c.OwningProcess -ne 0) {
                    try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
                }
            }
        } catch {}
    }
}

try {
    # Same acquisition order as startup: MCP before Tunnel.
    $locks+=Enter-TrainingLaunchLock $starterRoot 'mcp'
    $locks+=Enter-TrainingLaunchLock $starterRoot 'tunnel'
    foreach ($role in @('tunnel','mcp')) {
        if (-not (Stop-TrainingRole $starterRoot $role)) {
            Write-TrainingFail ("[FAIL] 식별 또는 종료 확인 필요: {0}; 기록 보존" -f $role)
            $failureCount++
            continue
        }

        # 포트 해제 폴링 (15초) → 미해제 시 포트 소유 PID 강제 종료 → 재폴링(5초)
        $ports = @(Get-TrainingPorts $role)
        $released = Wait-PortsReleased -Ports $ports -TimeoutSeconds 15
        if (-not $released) {
            $busy = Get-BusyPorts $ports
            Write-Host ("[WARN] {0} 포트 해제 지연 — 점유 중: {1}. 포트 소유 PID 강제 종료 시도." -f $role, ($busy -join ','))
            Stop-ProcessesByPort -Ports $busy
            Start-Sleep -Seconds 2
            $released = Wait-PortsReleased -Ports $ports -TimeoutSeconds 5
        }

        if ($released) {
            Write-Host ("[PASS] 종료 확인: {0}" -f $role)
        } else {
            $stillBusy = Get-BusyPorts $ports
            Write-TrainingFail ("[FAIL] {0} 포트 해제 실패 ({1}) — PC 재부팅을 권장합니다." -f $role, ($stillBusy -join ','))
            $failureCount++
        }
    }
}
catch { Write-TrainingFail '[FAIL] 시작 또는 종료가 진행 중이거나 상태 확인에 실패했습니다.'; $failureCount++ }
finally { foreach ($item in $locks) { Exit-TrainingLaunchLock $item } }

if ($failureCount -eq 0) { Write-Host 'STOP_RESULT: SUCCESS'; exit 0 }
Write-TrainingFail 'STOP_RESULT: FAIL'
exit 1
