param(
    # Use SSH tunnel mode (ports 18xxx -> remote 8xxx) instead of local 8xxx
    [switch]$UseTunnel,
    # SSH alias for tunnel (only used when -UseTunnel is set)
    [string]$RemoteAlias = "t3610",
    # Skip the MCP health check step
    [switch]$SkipHealthCheck,
    # Fail fast instead of prompting when user interaction is required
    [switch]$NonInteractive,
    # Write config and (optionally) start tunnel, but do not launch Claude Desktop
    [switch]$SkipLaunchClaude
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
$hardenScript = Join-Path $scriptDir "harden-claude-mcp-config.ps1"
$tunnelScript  = Join-Path $scriptDir "start-claude-mcp-tunnel.ps1"
$healthScript  = Join-Path $scriptDir "check-claude-mcp-health.ps1"
$tunnelRegressionScript = Join-Path $scriptDir "test-start-claude-mcp-tunnel-regression.ps1"
$totalSteps = if ($UseTunnel) { 5 } else { 4 }

function Write-Step {
    param([int]$Number, [string]$Message)
    Write-Host ""
    Write-Host "[$Number/$totalSteps] $Message" -ForegroundColor Cyan
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

function Resolve-ClaudeExecutable {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Claude\Claude.exe"),
        (Join-Path $env:APPDATA "Programs\Claude\Claude.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\claude.exe")
    )

    foreach ($candidate in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

Write-Host ""
Write-Host "===  start-claude-ready  ===" -ForegroundColor Yellow
Write-Host "Mode: $(if ($UseTunnel) { 'tunnel (18xxx -> t3610)' } else { 'local (8xxx)' })"
Write-Host ""

# ── Step 1: Guard – Claude must not be running ─────────────────────────────
Write-Step 1 "Checking for running Claude processes..."

$claudeProcs = Get-Process -Name "claude" -ErrorAction SilentlyContinue
if ($claudeProcs) {
    if ($NonInteractive) {
        $ids = ($claudeProcs | Select-Object -ExpandProperty Id) -join ", "
        throw "Claude Desktop is running (PID(s): $ids). Quit Claude and rerun, or omit -NonInteractive to allow prompt mode."
    }

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

$hardenParams = @{}
if ($UseTunnel) { $hardenParams.UseTunnelPorts = $true }

& $hardenScript @hardenParams
$exitCode = Get-LastExitCodeOrZero
if ($exitCode -ne 0) {
    throw "harden-claude-mcp-config.ps1 exited with code $exitCode"
}

Write-Ok "Config hardened."

# ── Step 3: (Optional) Start SSH tunnel ───────────────────────────────────
if ($UseTunnel) {
    Write-Step 3 "Running tunnel bootstrap regression guard..."

    if (-not (Test-Path $tunnelRegressionScript)) {
        throw "Regression script not found: $tunnelRegressionScript"
    }

    & $tunnelRegressionScript
    $exitCode = Get-LastExitCodeOrZero
    if ($exitCode -ne 0) {
        throw "test-start-claude-mcp-tunnel-regression.ps1 exited with code $exitCode"
    }

    Write-Ok "Tunnel regression guard passed."

    Write-Step 4 "Starting SSH MCP tunnel -> $RemoteAlias..."

    & $tunnelScript -RemoteAlias $RemoteAlias -SkipLaunchClaude -SkipConfigUpdate -SkipHealthCheck
    $exitCode = Get-LastExitCodeOrZero
    if ($exitCode -ne 0) {
        throw "start-claude-mcp-tunnel.ps1 exited with code $exitCode"
    }

    Write-Ok "Tunnel is active."
}
else {
    Write-Host ""
    Write-Host "[3/$totalSteps] Tunnel regression + tunnel steps skipped (local mode)." -ForegroundColor DarkGray
}

# ── Step 4: Health check ───────────────────────────────────────────────────
if (-not $SkipHealthCheck) {
    $healthStep = if ($UseTunnel) { 5 } else { 4 }
    Write-Step $healthStep "Running MCP health checks..."

    $healthParams = @{}
    if ($UseTunnel) { $healthParams.UseTunnelPorts = $true }

    try {
        & $healthScript @healthParams
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
    $healthStep = if ($UseTunnel) { 5 } else { 4 }
    Write-Host ""
    Write-Host "[$healthStep/$totalSteps] Health check skipped." -ForegroundColor DarkGray
}

# ── Launch Claude ──────────────────────────────────────────────────────────
if (-not $SkipLaunchClaude) {
    Write-Host ""
    $claudeExe = Resolve-ClaudeExecutable
    if (Test-Path $claudeExe) {
        Start-Process -FilePath $claudeExe | Out-Null
        Write-Host "Claude Desktop launched." -ForegroundColor Green
    }
    else {
        Write-Warning "Claude executable not found in standard locations (LocalAppData, AppData, WinGet links)."
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
