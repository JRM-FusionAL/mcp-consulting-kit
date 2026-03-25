param(
    [string]$TaskName = "MCP-Ops-Monitor",
    [string]$RemoteAlias = "t3610",
    [string]$RepoRoot = "",
    [switch]$SkipRemoteHostChecks,
    [switch]$Uninstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host ("[{0}] {1}" -f $ts, $Message) -ForegroundColor DarkCyan
}

function Ensure-TaskSchedulerService {
    $svc = Get-Service -Name "Schedule" -ErrorAction Stop
    if ($svc.Status -ne "Running") {
        Write-Host "Task Scheduler service is $($svc.Status). Starting..." -ForegroundColor Yellow
        Start-Service -Name "Schedule" -ErrorAction Stop
        $svc.WaitForStatus("Running", [TimeSpan]::FromSeconds(15))
    }
}

function Invoke-Schtasks {
    param(
        [string[]]$SchtasksArgs,
        [switch]$AllowFailure
    )

    $argText = ($SchtasksArgs -join " ")
    Write-Step ("schtasks.exe {0}" -f $argText)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $rawResult = & schtasks.exe @SchtasksArgs 2>&1
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $result = (($rawResult | ForEach-Object { $_.ToString() }) -join "`r`n")
    $code = $LASTEXITCODE
    if (($code -ne 0) -and (-not $AllowFailure)) {
        throw "schtasks.exe failed (exit $code): $result"
    }
    return $result.TrimEnd()
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
}

Write-Step "Starting scheduled task installer"
Write-Step ("TaskName={0}; RemoteAlias={1}; RepoRoot={2}; Uninstall={3}" -f $TaskName, $RemoteAlias, $RepoRoot, $Uninstall)

$scriptPath = Join-Path $PSScriptRoot "monitor-mcp-stack.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "monitor script missing: $scriptPath"
}

if ($Uninstall) {
    Write-Step "Uninstall mode"
    Ensure-TaskSchedulerService

    $deleteOutput = Invoke-Schtasks -SchtasksArgs @("/Delete", "/TN", $TaskName, "/F") -AllowFailure
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Scheduled task removed: $TaskName"
    }
    else {
        Write-Host "Scheduled task not found or could not be removed: $TaskName"
        if ($deleteOutput) {
            Write-Host $deleteOutput
        }
    }

    exit 0
}

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", ('"{0}"' -f $scriptPath),
    "-RemoteAlias", $RemoteAlias,
    "-RepoRoot", ('"{0}"' -f $RepoRoot),
    "-Quiet"
)

if ($SkipRemoteHostChecks) {
    $argList += "-SkipRemoteHostChecks"
}

Write-Step "Building scheduled task definition"
$taskCommand = "powershell.exe " + ($argList -join " ")

Write-Step "Ensuring Task Scheduler service is running"
Ensure-TaskSchedulerService

Write-Step "Removing existing task before registration (if present)"
Invoke-Schtasks -SchtasksArgs @("/Delete", "/TN", $TaskName, "/F") -AllowFailure | Out-Null

try {
    Write-Step "Registering scheduled task"
    Invoke-Schtasks -SchtasksArgs @("/Create", "/TN", $TaskName, "/SC", "MINUTE", "/MO", "5", "/TR", $taskCommand, "/F") | Out-Null
    Write-Step "Scheduled task registration complete"
}
catch {
    throw "Failed to register scheduled task '$TaskName'. Try running PowerShell as Administrator. Underlying error: $($_.Exception.Message)"
}

Write-Step "Reading scheduled task status"
$taskQuery = Invoke-Schtasks -SchtasksArgs @("/Query", "/TN", $TaskName, "/V", "/FO", "LIST")
$logsPath = Join-Path $RepoRoot "logs\mcp-ops-monitor.log"

Write-Host "Scheduled task installed: $TaskName"
Write-Host "Script: $scriptPath"
Write-Host "RepoRoot: $RepoRoot"
Write-Host "RemoteAlias: $RemoteAlias"
Write-Host "Interval: every 5 minutes"
Write-Host ""
Write-Host "Verification:" -ForegroundColor Cyan
$statusLines = ($taskQuery -split "`r?`n") |
    Where-Object { $_ -match "^(TaskName|Status|Next Run Time|Last Run Time|Last Result):" }
if ($statusLines.Count -gt 0) {
    $statusLines | ForEach-Object { Write-Host ("  {0}" -f $_) }
}
else {
    Write-Host "  (Could not parse status fields from schtasks output; task registration succeeded.)"
}
Write-Host ("  Log path:   {0}" -f $logsPath)
Write-Host ""
Write-Host "Quick checks:" -ForegroundColor Cyan
Write-Host ('  schtasks /Query /TN "{0}" /V /FO LIST' -f $TaskName)
Write-Host ('  schtasks /Run /TN "{0}"' -f $TaskName)
Write-Host ('  Get-Content "{0}" -Tail 10' -f $logsPath)
