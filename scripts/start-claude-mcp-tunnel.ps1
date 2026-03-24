param(
    [string]$RemoteAlias = "t3610",
    [switch]$SkipLaunchClaude,
    [switch]$ForceRestart,
    [switch]$SkipConfigUpdate,
    [switch]$SkipHealthCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TunnelPorts = @(18009, 18101, 18102, 18103)
$scriptDir = $PSScriptRoot
$hardenScript = Join-Path $scriptDir "harden-claude-mcp-config.ps1"
$healthScript = Join-Path $scriptDir "check-claude-mcp-health.ps1"

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

function Get-LastExitCodeOrZero {
    if (Test-Path variable:LASTEXITCODE) {
        return $LASTEXITCODE
    }

    return 0
}

function Get-TunnelProcesses {
    $owningIds = Get-NetTCPConnection -State Listen -LocalPort $TunnelPorts -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique

    if (-not $owningIds) {
        return @()
    }

    Get-Process -Id $owningIds -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -match "^ssh$" }
}

if (-not $SkipConfigUpdate) {
    & $hardenScript -UseTunnelPorts
    $exitCode = Get-LastExitCodeOrZero
    if ($exitCode -ne 0) {
        throw "harden-claude-mcp-config.ps1 exited with code $exitCode"
    }
}

if ($ForceRestart) {
    $existing = Get-TunnelProcesses
    if ($existing) {
        foreach ($proc in $existing) {
            Stop-Process -Id $proc.Id -Force
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
        "-L", "18009:localhost:8089",
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

if (-not $SkipHealthCheck) {
    & $healthScript -UseTunnelPorts -Quiet
    $exitCode = Get-LastExitCodeOrZero
    if ($exitCode -ne 0) {
        throw "check-claude-mcp-health.ps1 exited with code $exitCode"
    }
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
