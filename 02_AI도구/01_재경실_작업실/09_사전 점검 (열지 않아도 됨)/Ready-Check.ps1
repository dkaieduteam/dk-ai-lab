[CmdletBinding()]
param(
    [string]$Shot = ''      # 점검이 끝나면 창을 이 PNG 로 찍고 닫는다 (확인용)
)

# 교육 전 사전 점검 창 — 교안-세트 skill 공통 틀 (.claude/skills/교안-세트/assets/사전점검_GUI/)
# 과정마다 바꾸는 것 = 같은 폴더의 준비점검_설정.json 과 점검 스크립트뿐. 이 파일은 고치지 않고 복사한다.
# 이 파일은 UTF-8(BOM) 으로 저장한다. Windows PowerShell 5.1 이 BOM 없는 UTF-8 을 cp949 로 읽어 한글이 깨진다.
#
# 점검 스크립트와 주고받는 약속 : 스크립트는 --gui 를 받으면 줄마다 아래처럼 찍는다 (그 밖의 줄은 무시)
#   @@ {"key": "place", "s": "ok|no|warn", "d": "설명", "fix": "해결 방법(없으면 빈 글자)", "link": {"text": "설치 페이지 열기", "url": "https://…"}}
#   (link 는 선택. 있으면 그 줄 오른쪽에 누르면 열리는 링크를 둔다)
#   @@ {"done": true, "tail": "마지막 안내", "result": "결과 파일 이름(작업실 바로 아래)"}

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -Namespace RC -Name Dpi -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();' -ErrorAction SilentlyContinue
try { [void][RC.Dpi]::SetProcessDPIAware() } catch { }
[System.Windows.Forms.Application]::EnableVisualStyles()

$setupDir = $PSScriptRoot
$root = Split-Path -Parent $setupDir
$cfg = Get-Content (Join-Path $setupDir '준비점검_설정.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$items = @($cfg.항목)

# ---------- 색 · 글꼴 (DESIGN.md: Dongkuk Navy Pop) ----------
function C([string]$hex) { [System.Drawing.ColorTranslator]::FromHtml($hex) }
$navy = C '#002452'; $red = C '#C51F2A'; $ink = C '#1a2233'; $mute = C '#5b6b82'; $line = C '#dfe4ec'; $soft = C '#eef1f6'; $green = C '#1f7a4d'
$badge = @{
    ok   = @{ T = '통과';      B = (C '#e3f3ea'); F = $green }
    no   = @{ T = '실패';      B = (C '#fbe6e7'); F = $red }
    warn = @{ T = '확인 필요'; B = (C '#fdf0dc'); F = (C '#b26a00') }
    wait = @{ T = '점검 중…';  B = (C '#eef0f3'); F = (C '#6b7686') }
    skip = @{ T = '건너뜀';    B = (C '#eef0f3'); F = (C '#6b7686') }
}
$fontName = 'Malgun Gothic'
$fBody = New-Object System.Drawing.Font($fontName, 9.5)
$fName = New-Object System.Drawing.Font($fontName, 11, [System.Drawing.FontStyle]::Bold)
$fSmall = New-Object System.Drawing.Font($fontName, 8.5)
$fBadge = New-Object System.Drawing.Font($fontName, 9, [System.Drawing.FontStyle]::Bold)
$fBtn = New-Object System.Drawing.Font($fontName, 9.5, [System.Drawing.FontStyle]::Bold)

function New-Btn([string]$text, [bool]$primary) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $text; $b.Font = $fBtn; $b.FlatStyle = 'Flat'; $b.Cursor = 'Hand'
    $b.FlatAppearance.BorderColor = $navy; $b.FlatAppearance.BorderSize = 1
    if ($primary) { $b.BackColor = $navy; $b.ForeColor = [System.Drawing.Color]::White }
    else { $b.BackColor = [System.Drawing.Color]::White; $b.ForeColor = $navy }
    return $b
}

# ---------- 점검 프로그램 찾기 ----------
function Find-First([string[]]$patterns) {
    foreach ($p in $patterns) {
        $hit = Get-ChildItem (Join-Path $root $p) -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}
$py = Find-First @($cfg.python)
if (-not $py) { foreach ($n in @($cfg.python_명령)) { $g = Get-Command $n -ErrorAction SilentlyContinue | Select-Object -First 1; if ($g) { $py = $g.Source; break } } }
$script = Find-First @($cfg.점검)

# ---------- 창 ----------
$W = 760; $rowH = 62
$groups = @($items | ForEach-Object { $_.group } | Select-Object -Unique).Count
$listH = [Math]::Min(600, 8 + $items.Count * $rowH + $groups * 24)
$form = New-Object System.Windows.Forms.Form
$form.Text = [string]$cfg.제목
$form.AutoScaleDimensions = New-Object System.Drawing.SizeF(96, 96)
$form.AutoScaleMode = 'Dpi'
$guide = $cfg.교안          # 선택 : {"이름": "...", "주소": "https://..."} 이 있으면 창 아래에 교안 링크를 둔다
$guideH = if ($guide -and $guide.주소) { 34 } else { 0 }
$form.ClientSize = New-Object System.Drawing.Size($W, (116 + $listH + 120 + $guideH))
$form.StartPosition = 'CenterScreen'
$form.BackColor = [System.Drawing.Color]::White
$form.Font = $fBody
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox = $false

$head = New-Object System.Windows.Forms.Panel
$head.SetBounds(0, 0, $W, 72); $head.BackColor = $navy
$t1 = New-Object System.Windows.Forms.Label
$t1.Text = [string]$cfg.제목; $t1.ForeColor = [System.Drawing.Color]::White
$t1.Font = New-Object System.Drawing.Font($fontName, 15, [System.Drawing.FontStyle]::Bold); $t1.SetBounds(22, 10, 700, 32)
$t2 = New-Object System.Windows.Forms.Label
$t2.Text = '점검을 시작합니다…'; $t2.ForeColor = C '#c9d3e3'; $t2.Font = $fSmall; $t2.SetBounds(24, 43, 700, 20)
$head.Controls.AddRange(@($t1, $t2))
$form.Controls.Add($head)

$sum = New-Object System.Windows.Forms.Panel
$sum.SetBounds(0, 72, $W, 44); $sum.BackColor = $soft
$sumL = New-Object System.Windows.Forms.Label
$sumL.Font = New-Object System.Drawing.Font($fontName, 11, [System.Drawing.FontStyle]::Bold); $sumL.ForeColor = $ink; $sumL.SetBounds(22, 10, 110, 24)
$bar = New-Object System.Windows.Forms.Panel; $bar.SetBounds(134, 17, 430, 10); $bar.BackColor = C '#d5dbe5'
$fill = New-Object System.Windows.Forms.Panel; $fill.SetBounds(0, 0, 0, 10); $fill.BackColor = $navy; $bar.Controls.Add($fill)
$sumR = New-Object System.Windows.Forms.Label
$sumR.Font = $fBadge; $sumR.ForeColor = $red; $sumR.TextAlign = 'MiddleRight'; $sumR.SetBounds(570, 10, 168, 24)
$sum.Controls.AddRange(@($sumL, $bar, $sumR))
$form.Controls.Add($sum)

$list = New-Object System.Windows.Forms.Panel
$list.SetBounds(0, 116, $W, $listH); $list.AutoScroll = $true; $list.BackColor = [System.Drawing.Color]::White
$form.Controls.Add($list)

$rows = @{}
$y = 4; $lastGroup = ''
foreach ($it in $items) {
    if ($it.group -ne $lastGroup) {
        $g = New-Object System.Windows.Forms.Label
        $g.Text = [string]$it.group; $g.Font = $fBadge; $g.ForeColor = $mute; $g.SetBounds(22, $y + 6, 300, 18)
        $list.Controls.Add($g); $y += 24; $lastGroup = $it.group
    }
    $b = New-Object System.Windows.Forms.Label
    $b.Font = $fBadge; $b.TextAlign = 'MiddleCenter'; $b.SetBounds(22, $y + 17, 88, 24)
    $n = New-Object System.Windows.Forms.Label
    $n.Text = [string]$it.name; $n.Font = $fName; $n.ForeColor = $ink; $n.SetBounds(124, $y + 4, 440, 22)
    $d = New-Object System.Windows.Forms.Label
    $d.Font = $fSmall; $d.ForeColor = $mute; $d.SetBounds(125, $y + 26, 600, 34)
    $lk = New-Object System.Windows.Forms.LinkLabel
    $lk.Font = $fBadge; $lk.LinkColor = $navy; $lk.TextAlign = 'MiddleRight'; $lk.SetBounds(566, $y + 4, 168, 22); $lk.Visible = $false
    $lk.Add_LinkClicked({ param($sender, $e) if ($sender.Tag) { Start-Process ([string]$sender.Tag) } })
    $sep = New-Object System.Windows.Forms.Panel; $sep.SetBounds(0, $y + $rowH - 1, $W - 22, 1); $sep.BackColor = $line
    $list.Controls.AddRange(@($b, $n, $d, $lk, $sep))
    $rows[[string]$it.key] = @{ Badge = $b; Detail = $d; Link = $lk; Status = 'wait' }
    $y += $rowH
}

function Set-Link([string]$k, $link) {
    if (-not $rows.ContainsKey($k)) { return }
    $lk = $rows[$k].Link
    if ($link -and $link.url) {
        $lk.Text = if ($link.text) { [string]$link.text } else { '열기' }
        $lk.Tag = [string]$link.url; $lk.Visible = $true
    } else { $lk.Visible = $false; $lk.Tag = $null }
}
function Set-Row([string]$k, [string]$s, [string]$detail) {
    if (-not $rows.ContainsKey($k)) { return }
    $r = $rows[$k]
    if ($r.Status -eq 'no' -and $s -ne 'wait') { $s = 'no' }   # 한 항목에 여러 줄이 오면 실패를 남긴다
    $bd = $badge[$s]
    $r.Status = $s; $r.Badge.Text = $bd.T; $r.Badge.BackColor = $bd.B; $r.Badge.ForeColor = $bd.F
    if ($null -ne $detail) { $r.Detail.Text = $detail }
    $r.Detail.ForeColor = if ($s -eq 'no') { $red } else { $mute }
}

$by = 116 + $listH + 8
$log = New-Object System.Windows.Forms.Label
$log.Font = $fBody; $log.ForeColor = $ink; $log.SetBounds(22, $by, 716, 56)
$form.Controls.Add($log)

$reBtn = New-Btn '다시 점검' $true; $reBtn.SetBounds(22, $by + 64, 120, 36)
$openBtn = New-Btn '결과 파일 열기' $false; $openBtn.SetBounds(152, $by + 64, 140, 36)
$copyBtn = New-Btn '결과 복사' $false; $copyBtn.SetBounds(302, $by + 64, 110, 36)
$copyL = New-Object System.Windows.Forms.Label
$copyL.Font = $fSmall; $copyL.ForeColor = $mute; $copyL.TextAlign = 'MiddleLeft'; $copyL.SetBounds(420, $by + 64, 318, 36)
$form.Controls.AddRange(@($reBtn, $openBtn, $copyBtn, $copyL))

if ($guideH) {
    $gL = New-Object System.Windows.Forms.Label
    $gL.Text = '교안'; $gL.Font = $fBadge; $gL.ForeColor = $mute; $gL.SetBounds(22, $by + 112, 44, 22)
    $gLink = New-Object System.Windows.Forms.LinkLabel
    $gName = if ($guide.이름) { [string]$guide.이름 } else { [string]$guide.주소 }
    $gLink.Text = $gName; $gLink.Font = $fBody; $gLink.LinkColor = $navy; $gLink.SetBounds(68, $by + 110, 670, 24)
    $gLink.Add_LinkClicked({ Start-Process ([string]$guide.주소) })
    $form.Controls.AddRange(@($gL, $gLink))
}

$script:resultPath = $null
$openBtn.Add_Click({ if ($script:resultPath -and (Test-Path $script:resultPath)) { Start-Process notepad.exe -ArgumentList ('"{0}"' -f $script:resultPath) } })
$copyBtn.Add_Click({
    if ($script:resultPath -and (Test-Path $script:resultPath)) {
        [System.Windows.Forms.Clipboard]::SetText((Get-Content $script:resultPath -Raw -Encoding UTF8))
        $copyL.Text = '복사했습니다'
    }
})
$reBtn.Add_Click({ Start-Check })

function Update-Summary {
    $done = @($rows.Keys | Where-Object { $rows[$_].Status -eq 'ok' }).Count   # 확인 필요는 통과로 세지 않는다
    $sumL.Text = ('통과 {0} / {1}' -f $done, $rows.Count)
    $fill.Width = [int](430 * $done / [Math]::Max(1, $rows.Count))
    $bad = @($rows.Keys | Where-Object { $rows[$_].Status -eq 'no' }).Count
    $warn = @($rows.Keys | Where-Object { $rows[$_].Status -eq 'warn' }).Count
    if ($script:busy) { $sumR.ForeColor = $mute; $sumR.Text = '점검 중' }
    elseif ($bad) { $sumR.ForeColor = $red; $sumR.Text = ('해결할 것 {0}개' -f $bad) }
    elseif ($warn) { $sumR.ForeColor = C '#b26a00'; $sumR.Text = ('확인할 것 {0}개' -f $warn) }
    else { $sumR.ForeColor = $green; $sumR.Text = '준비 끝' }
    $reBtn.Enabled = -not $script:busy
    $has = [bool]($script:resultPath -and (Test-Path $script:resultPath))
    $openBtn.Enabled = (-not $script:busy) -and $has; $copyBtn.Enabled = $openBtn.Enabled
}

# ---------- 점검 실행 (출력은 임시 파일로 받아 타이머로 읽는다, 창이 멈추지 않게) ----------
$script:busy = $false; $script:proc = $null; $script:outFile = $null; $script:readPos = 0; $script:checkCount = 0
function Start-Check {
    if ($script:busy) { return }
    foreach ($k in @($rows.Keys)) { $rows[$k].Status = 'wait'; Set-Row $k 'wait' ''; Set-Link $k $null }
    $log.Text = ''; $copyL.Text = ''
    if (-not $py -or -not $script) {
        foreach ($k in @($rows.Keys)) { Set-Row $k 'skip' '' }
        $log.ForeColor = $red
        $log.Text = '점검 프로그램을 찾지 못했습니다. 처음 받은 zip 파일을 마우스 오른쪽 → "압축 풀기"로 다시 푼 뒤 실행하세요'
        Update-Summary; $script:checkCount++; return
    }
    $script:busy = $true; $log.ForeColor = $ink
    $t2.Text = ('점검 중… {0}' -f [string]$cfg.부제)
    $script:outFile = Join-Path $env:TEMP ('aiedu_ready_{0}_{1}.txt' -f $PID, $script:checkCount)
    $script:readPos = 0
    $env:PYTHONIOENCODING = 'utf-8'
    $script:proc = Start-Process -FilePath $py -ArgumentList @('-I', '-B', '-X', 'utf8', ('"{0}"' -f $script), '--gui') `
        -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput $script:outFile -RedirectStandardError ($script:outFile + '.err')
    Update-Summary
}
function Read-NewLines {
    if (-not $script:outFile -or -not (Test-Path $script:outFile)) { return @() }
    try {
        $fs = New-Object IO.FileStream($script:outFile, 'Open', 'Read', 'ReadWrite')
        [void]$fs.Seek($script:readPos, 'Begin')
        $sr = New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8)
        $txt = $sr.ReadToEnd(); $sr.Close()
    } catch { return @() }
    $cut = $txt.LastIndexOf("`n")
    if ($cut -lt 0) { return @() }
    $script:readPos += [Text.Encoding]::UTF8.GetByteCount($txt.Substring(0, $cut + 1))
    return @($txt.Substring(0, $cut + 1) -split "`r?`n" | Where-Object { $_ -like '@@ *' })
}
function Use-Lines([string[]]$ls) {
    foreach ($l in $ls) {
        try { $m = $l.Substring(3) | ConvertFrom-Json } catch { continue }
        if ($m.done) {
            $log.Text = [string]$m.tail
            $log.ForeColor = if ($m.tail -match '실패') { $red } else { $ink }
            if ($m.result) { $script:resultPath = Join-Path $root ([string]$m.result) }
            continue
        }
        $txt = [string]$m.d
        if ($m.fix) { $txt += "`n→ " + [string]$m.fix }
        Set-Row ([string]$m.key) ([string]$m.s) $txt
        if ($m.link) { Set-Link ([string]$m.key) $m.link }
    }
}
function Complete-Check {
    Use-Lines (Read-NewLines)
    $code = $script:proc.ExitCode
    $script:proc = $null
    foreach ($k in @($rows.Keys)) { if ($rows[$k].Status -eq 'wait') { Set-Row $k 'skip' '앞 항목을 먼저 해결하면 점검합니다' } }
    if (-not $log.Text) {
        $err = ''
        if (Test-Path ($script:outFile + '.err')) { $err = (Get-Content ($script:outFile + '.err') -Raw -Encoding UTF8) }
        $log.ForeColor = $red
        $msg = ('점검이 끝까지 돌지 못했습니다 (종료 코드 {0}). {1}' -f $code, ([string]$err -replace '\s+', ' ').Trim())
        $log.Text = $msg.Substring(0, [Math]::Min(300, $msg.Length))
    }
    Remove-Item $script:outFile, ($script:outFile + '.err') -Force -ErrorAction SilentlyContinue
    $t2.Text = ('마지막 점검 {0} · 실습 폴더는 바꾸지 않습니다' -f (Get-Date -Format 'yyyy-MM-dd HH:mm'))
    $script:busy = $false; $script:checkCount++
    Update-Summary
}

# ---------- 타이머 ----------
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 400
$script:shotDone = $false
$timer.Add_Tick({
    if ($script:proc) {
        Use-Lines (Read-NewLines); Update-Summary
        if ($script:proc.HasExited) { $script:proc.WaitForExit(); Complete-Check }
    }
    if ($Shot -and $script:checkCount -ge 1 -and -not $script:busy -and -not $script:shotDone) {
        $script:shotDone = $true
        $form.Refresh()
        $bmp = New-Object System.Drawing.Bitmap($form.Width, $form.Height)
        $form.DrawToBitmap($bmp, (New-Object System.Drawing.Rectangle(0, 0, $form.Width, $form.Height)))
        $bmp.Save($Shot, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
        $form.Close()
    }
})
$form.Add_Shown({ $timer.Start(); Start-Check })
$form.Add_FormClosing({ if ($script:proc -and -not $script:proc.HasExited) { try { $script:proc.Kill() } catch { } } })

Update-Summary
[void]$form.ShowDialog()
$timer.Stop()
