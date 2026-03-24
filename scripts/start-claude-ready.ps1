param(
    # Use SSH tunnel mode (ports 18xxx -> remote 8xxx) instead of local 8xxx
    [switch]$UseTunnel,
    # SSH alias for tunnel (only used when -UseTunnel is set)
    [string]$RemoteAlias = "t3610",
    # Skip the MCP health check step
    [switch]$SkipHealthCheck,
    # Write config and (optionally) start tunnel, but do not launch Claude Desktop
    [switch]$SkipLaunchClaude
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
$hardenScript = Join-Path $scriptDir "harden-claude-mcp-config.ps1"
$tunnelScript  = Join-Path $scriptDir "start-claude-mcp-tunnel.ps1"
$healthScript  = Join-Path $scriptDir "check-claude-mcp-health.ps1"
$claudeExe     = Join-Path $env:LOCALAPPDATA "Programs\Claude\Claude.exe"

function Write-Step {
    param([int]$Number, [string]$Message)
    Write-Host ""
    Write-Host "[$Number/4] $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  OK  $Message" -ForegroundColor Green
}

function Get-LastExitCodeOrZero {
    if (Test-Path variable:LASTEXITCODE) {
        return $LASTEXITCODE
    }

    return 0
}

Write-Host ""
Write-Host "===  start-claude-ready  ===" -ForegroundColor Yellow
Write-Host "Mode: $(if ($UseTunnel) { 'tunnel (18xxx -> t3610)' } else { 'local (8xxx)' })"
Write-Host ""

# ── Step 1: Guard – Claude must not be running ─────────────────────────────
Write-Step 1 "Checking for running Claude processes..."

$claudeProcs = Get-Process -Name "claude" -ErrorAction SilentlyContinue
if ($claudeProcs) {
    Write-Host ""
    Write-Host "  Claude Desktop is still running ($($claudeProcs.Count) process(es))." -ForegroundColor Yellow
    Write-Host "  Please fully quit Claude Desktop (File > Quit or system tray > Quit),"
    Write-Host "  then press Enter to continue, or Ctrl+C to abort."
    $null = Read-Host

    # Re-check after user says they quit
    $claudeProcs = Get-Process -Name "claude" -ErrorAction SilentlyContinue
    if ($claudeProcs) {
        throw "Claude Desktop is still running. Quit it completely and rerun this script."
    }
}

Write-Ok "Claude Desktop is not running."

# ── Step 2: Harden the MCP config ─────────────────────────────────────────
Write-Step 2 "Hardening Claude Desktop MCP config..."

$hardenArgs = @()
if ($UseTunnel) { $hardenArgs += "-UseTunnelPorts" }

& $hardenScript @hardenArgs
$exitCode = Get-LastExitCodeOrZero
if ($exitCode -ne 0) {
    throw "harden-claude-mcp-config.ps1 exited with code $exitCode"
}

Write-Ok "Config hardened."

# ── Step 3: (Optional) Start SSH tunnel ───────────────────────────────────
if ($UseTunnel) {
    Write-Step 3 "Starting SSH MCP tunnel -> $RemoteAlias..."

    & $tunnelScript -RemoteAlias $RemoteAlias -SkipLaunchClaude -SkipConfigUpdate -SkipHealthCheck
    $exitCode = Get-LastExitCodeOrZero
    if ($exitCode -ne 0) {
        throw "start-claude-mcp-tunnel.ps1 exited with code $exitCode"
    }

    Write-Ok "Tunnel is active."
}
else {
    Write-Host ""
    Write-Host "[3/4] Tunnel step skipped (local mode)." -ForegroundColor DarkGray
}

# ── Step 4: Health check ───────────────────────────────────────────────────
if (-not $SkipHealthCheck) {
    Write-Step 4 "Running MCP health checks..."

    $healthArgs = @()
    if ($UseTunnel) { $healthArgs += "-UseTunnelPorts" }

    try {
        & $healthScript @healthArgs
        $exitCode = Get-LastExitCodeOrZero
        if ($exitCode -ne 0) {
            throw "check-claude-mcp-health.ps1 exited with code $exitCode"
        }
        Write-Ok "All MCP endpoints reachable."
    }
    catch {
        Write-Host ""
        Write-Warning "Health check failed: $_"
        Write-Host "  MCP servers may not be running yet. Start them and rerun, or pass -SkipHealthCheck."
        Write-Host ""
        $answer = Read-Host "Continue and launch Claude anyway? [y/N]"
        if ($answer -notmatch "^[Yy]") {
            throw "Aborted by user after health-check failure."
        }
    }
}
else {
    Write-Host ""
    Write-Host "[4/4] Health check skipped." -ForegroundColor DarkGray
}

# ── Launch Claude ──────────────────────────────────────────────────────────
if (-not $SkipLaunchClaude) {
    Write-Host ""
    if (Test-Path $claudeExe) {
        Start-Process -FilePath $claudeExe | Out-Null
        Write-Host "Claude Desktop launched." -ForegroundColor Green
    }
    else {
        Write-Warning "Claude executable not found at: $claudeExe"
        Write-Warning "Launch Claude Desktop manually."
    }
}
else {
    Write-Host ""
    Write-Host "Launch step skipped (-SkipLaunchClaude)." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "===  Done  ===" -ForegroundColor Yellow
Write-Host ""
