param(
    [string]$RemoteAlias = "t3610",
    [switch]$SkipLaunchClaude,
    [switch]$ForceRestart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TunnelPorts = @(18009, 18101, 18102, 18103)
$TunnelArgSignature = "18009:localhost:8009"

function Test-PortListening {
    param([int]$Port)

    try {
        Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Get-TunnelProcesses {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "^ssh(\\.exe)?$" -and
            $_.CommandLine -like "*$TunnelArgSignature*"
        }
}

if ($ForceRestart) {
    $existing = Get-TunnelProcesses
    if ($existing) {
        foreach ($proc in $existing) {
            Stop-Process -Id $proc.ProcessId -Force
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
    $sshArgs = @(
        "-N",
        "-L", "18009:localhost:8009",
        "-L", "18101:localhost:8101",
        "-L", "18102:localhost:8102",
        "-L", "18103:localhost:8103",
        $RemoteAlias
    )

    Start-Process -FilePath "ssh" -ArgumentList $sshArgs -WindowStyle Minimized | Out-Null
    Start-Sleep -Seconds 2
}

$results = foreach ($port in $TunnelPorts) {
    [PSCustomObject]@{
        Port = $port
        Listening = (Test-PortListening -Port $port)
    }
}

$results | Format-Table -AutoSize

if ($results.Listening -contains $false) {
    throw "One or more tunnel ports are not active."
}

if (-not $SkipLaunchClaude) {
    $claudeExe = Join-Path $env:LOCALAPPDATA "Programs\\Claude\\Claude.exe"
    if (Test-Path $claudeExe) {
        Start-Process -FilePath $claudeExe | Out-Null
        Write-Host "Claude Desktop launched."
    }
    else {
        Write-Warning "Claude executable not found at $claudeExe"
    }
}

Write-Host "MCP tunnel is active."
