param(
    [string]$RemoteAlias = "t3610",
    [switch]$SkipLaunchClaude,
    [switch]$ForceRestart,
    [switch]$SkipConfigUpdate,
    [switch]$SkipHealthCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TunnelPorts = @(18009, 18101, 18102, 18103, 18104)
$scriptDir = $PSScriptRoot
$hardenScript = Join-Path $scriptDir "harden-claude-mcp-config.ps1"
$healthScript = Join-Path $scriptDir "check-claude-mcp-health.ps1"
$sshLaunchOutputText = ""

function Write-Step {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host ("[{0}] {1}" -f $ts, $Message) -ForegroundColor DarkCyan
}

function Get-ListeningOwningProcessIds {
    param([int[]]$Ports)

    $portLookup = @{}
    foreach ($p in $Ports) {
        $portLookup[[string]$p] = $true
    }

    $pidLookup = @{}
    $lines = & netstat -ano -p tcp 2>$null
    foreach ($line in $lines) {
        if ($line -match '^\s*TCP\s+\S+:(\d+)\s+\S+\s+LISTENING\s+(\d+)\s*$') {
            $port = $matches[1]
            $processIdText = $matches[2]
            if ($portLookup.ContainsKey($port)) {
                $pidLookup[$processIdText] = $true
            }
        }
    }

    return @($pidLookup.Keys | ForEach-Object { [int]$_ })
}

function Test-PortListening {
    param([int]$Port)

    try {
        $pids = Get-ListeningOwningProcessIds -Ports @($Port)
        return ($pids.Count -gt 0)
    }
    catch {
        return $false
    }
}

function Get-TunnelProcesses {
    $owningIds = Get-ListeningOwningProcessIds -Ports $TunnelPorts

    if (-not $owningIds) {
        return @()
    }

    Get-Process -Id $owningIds -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -match "^ssh$" }
}

function Test-SshPreflight {
    param([string]$RemoteAlias)

    $sshCommand = Get-Command ssh -ErrorAction SilentlyContinue
    if (-not $sshCommand) {
        throw "ssh executable not found in PATH. Install OpenSSH client or add it to PATH."
    }

    # BatchMode prevents password prompts so failures are immediate and script-friendly.
    $probeOutput = & ssh -o BatchMode=yes -o ConnectTimeout=8 $RemoteAlias "echo tunnel-preflight-ok" 2>&1
    $probeExitCode = $LASTEXITCODE
    $probeText = (($probeOutput | ForEach-Object { $_.ToString() }) -join "`r`n").Trim()

    if ($probeExitCode -ne 0) {
        throw "SSH preflight failed for alias '$RemoteAlias' (exit $probeExitCode). Output: $probeText"
    }

    if ($probeText -notmatch "tunnel-preflight-ok") {
        Write-Warning "SSH preflight succeeded but probe marker was not observed. Continuing. Output: $probeText"
    }
}

function Get-InactiveTunnelPorts {
    param([int[]]$Ports)

    $inactive = @()
    foreach ($port in $Ports) {
        if (-not (Test-PortListening -Port $port)) {
            $inactive += $port
        }
    }
    return @($inactive)
}

Write-Step ("Starting tunnel bootstrap for alias '{0}'" -f $RemoteAlias)

if (-not $SkipConfigUpdate) {
    Write-Step "Applying Claude MCP config hardening for tunnel mode"
    & $hardenScript -UseTunnelPorts
}

if ($ForceRestart) {
    Write-Step "ForceRestart enabled; stopping existing ssh tunnel processes"
    $existing = @(Get-TunnelProcesses)
    Write-Step ("Found {0} ssh process(es) listening on tunnel ports" -f $existing.Count)
    if ($existing) {
        foreach ($proc in $existing) {
            Write-Step ("Stopping ssh PID {0}" -f $proc.Id)
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            }
            catch {
                Write-Warning ("Failed stopping PID {0}: {1}" -f $proc.Id, $_.Exception.Message)
            }
        }
        Start-Sleep -Seconds 1
    }
}

$missingPorts = @()
foreach ($port in $TunnelPorts) {
    if (-not (Test-PortListening -Port $port)) {
        $missingPorts += $port
    }
}

if ($missingPorts.Count -gt 0) {
    Write-Step ("Missing local tunnel ports: {0}" -f ($missingPorts -join ", "))
    Write-Step "Running SSH connectivity preflight"
    Test-SshPreflight -RemoteAlias $RemoteAlias

    Write-Step "Starting SSH local-forwards"
    $sshArgs = @(
        "-o", "BatchMode=yes",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ConnectTimeout=8",
        "-N",
        "-L", "18009:localhost:8089",
        "-L", "18101:localhost:8101",
        "-L", "18102:localhost:8102",
        "-L", "18103:localhost:8103",
        "-L", "18104:localhost:8104",
        $RemoteAlias
    )

    $sshOutLog = Join-Path $env:TEMP "mcp-tunnel-ssh.out.log"
    $sshErrLog = Join-Path $env:TEMP "mcp-tunnel-ssh.err.log"
    Remove-Item -Path $sshOutLog, $sshErrLog -ErrorAction SilentlyContinue

    $sshProc = Start-Process -FilePath "ssh" -ArgumentList $sshArgs -WindowStyle Minimized -PassThru -RedirectStandardOutput $sshOutLog -RedirectStandardError $sshErrLog
    Start-Sleep -Seconds 1

    if ($sshProc.HasExited) {
        $stderrNow = if (Test-Path $sshErrLog) { ((Get-Content -Path $sshErrLog -ErrorAction SilentlyContinue) -join "`n").Trim() } else { "" }
        $stdoutNow = if (Test-Path $sshOutLog) { ((Get-Content -Path $sshOutLog -ErrorAction SilentlyContinue) -join "`n").Trim() } else { "" }
        $sshLaunchOutputText = (($stderrNow, $stdoutNow | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join "`n").Trim()
        if ([string]::IsNullOrWhiteSpace($sshLaunchOutputText)) {
            $sshLaunchOutputText = "(no stdout/stderr output captured)"
        }
        throw "ssh tunnel process exited early (exit $($sshProc.ExitCode)). Output: $sshLaunchOutputText"
    }

    # Give forwards time to initialize; remote alias + DNS/route can take a few seconds.
    $maxWaitSeconds = 15
    for ($i = 1; $i -le $maxWaitSeconds; $i++) {
        $stillMissing = @(Get-InactiveTunnelPorts -Ports $TunnelPorts)

        if ($stillMissing.Count -eq 0) {
            Write-Step ("All tunnel ports became active after {0}s" -f $i)
            break
        }

        Start-Sleep -Seconds 1
    }

    # Fallback path for environments where Start-Process + redirected stdio can interfere with ssh startup.
    $afterPrimaryMissing = @(Get-InactiveTunnelPorts -Ports $TunnelPorts)
    if ($afterPrimaryMissing.Count -gt 0) {
        Write-Step ("Primary SSH launch did not activate ports. Fallback launch via cmd.exe start. Missing: {0}" -f ($afterPrimaryMissing -join ", "))

        # Fallback launch without stdout/stderr redirection; this avoids hangs/validation quirks
        # seen with some Windows PowerShell + cmd/start combinations.
        Start-Process -FilePath "ssh" -ArgumentList $sshArgs -WindowStyle Minimized | Out-Null

        for ($j = 1; $j -le $maxWaitSeconds; $j++) {
            $stillMissing = @(Get-InactiveTunnelPorts -Ports $TunnelPorts)
            if ($stillMissing.Count -eq 0) {
                Write-Step ("Fallback SSH launch activated all tunnel ports after {0}s" -f $j)
                break
            }
            Start-Sleep -Seconds 1
        }
    }
}
else {
    Write-Step "All tunnel ports already listening; skipping ssh spawn"
}

$results = foreach ($port in $TunnelPorts) {
    [PSCustomObject]@{
        Port = $port
        Listening = (Test-PortListening -Port $port)
    }
}

$results | Format-Table -AutoSize

if ($results.Listening -contains $false) {
    $inactive = ($results | Where-Object { -not $_.Listening } | Select-Object -ExpandProperty Port) -join ", "

    $sshProcessState = ""
    $remainingSsh = @(Get-TunnelProcesses)
    if ($remainingSsh.Count -gt 0) {
        $sshProcessState = "ssh process still running on tunnel ports (PIDs: {0})" -f (($remainingSsh | Select-Object -ExpandProperty Id) -join ",")
    }
    else {
        $allSsh = @(Get-Process -Name "ssh" -ErrorAction SilentlyContinue)
        if ($allSsh.Count -gt 0) {
            $sshProcessState = "ssh process running but not listening on tunnel ports (PIDs: {0})" -f (($allSsh | Select-Object -ExpandProperty Id) -join ",")
        }
        else {
            $sshProcessState = "no running ssh process detected after launch"
        }
    }

    $detailParts = @()
    $detailParts += $sshProcessState
    if (-not [string]::IsNullOrWhiteSpace($sshLaunchOutputText)) { $detailParts += "ssh launch output: $sshLaunchOutputText" }

    $sshErrLogPath = Join-Path $env:TEMP "mcp-tunnel-ssh.err.log"
    $sshOutLogPath = Join-Path $env:TEMP "mcp-tunnel-ssh.out.log"
    if (Test-Path $sshErrLogPath) {
        $stderrTail = ((Get-Content -Path $sshErrLogPath -ErrorAction SilentlyContinue | Select-Object -Last 20) -join "`n").Trim()
        if (-not [string]::IsNullOrWhiteSpace($stderrTail)) { $detailParts += "ssh stderr: $stderrTail" }
    }
    if (Test-Path $sshOutLogPath) {
        $stdoutTail = ((Get-Content -Path $sshOutLogPath -ErrorAction SilentlyContinue | Select-Object -Last 20) -join "`n").Trim()
        if (-not [string]::IsNullOrWhiteSpace($stdoutTail)) { $detailParts += "ssh stdout: $stdoutTail" }
    }

    $detailText = if ($detailParts.Count -gt 0) { " " + ($detailParts -join " | ") } else { "" }

    throw "One or more tunnel ports are not active. Inactive ports: $inactive.$detailText"
}

if (-not $SkipHealthCheck) {
    Write-Step "Running tunnel health checks"
    & $healthScript -UseTunnelPorts -Quiet
}

if (-not $SkipLaunchClaude) {
    Write-Step "Launching Claude Desktop"
    $claudeExe = Join-Path $env:LOCALAPPDATA "Programs\\Claude\\Claude.exe"
    if (Test-Path $claudeExe) {
        Start-Process -FilePath $claudeExe | Out-Null
        Write-Host "Claude Desktop launched."
    }
    else {
        Write-Warning "Claude executable not found at $claudeExe"
    }
}

Write-Step "Tunnel bootstrap complete"
Write-Host "MCP tunnel is active."
