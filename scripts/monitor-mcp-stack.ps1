param(
    [string]$RemoteAlias = "t3610",
    [string]$RepoRoot = "",
    [int]$HttpTimeoutSec = 8,
    # Require more than one transient miss before escalating.
    [int]$P2ConsecutiveDown = 3,
    [int]$P1ConsecutiveDown = 6,
    # Health endpoint latency thresholds (single-probe basis).
    [int]$P2HealthLatencyMs = 1500,
    [int]$P1HealthLatencyMs = 3000,
    # Host pressure thresholds on t3610.
    [int]$P2MemoryPct = 90,
    [int]$P1MemoryPct = 97,
    [int]$P2DiskPct = 85,
    [int]$P1DiskPct = 95,
    [switch]$SkipRemoteHostChecks,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
}

$logsDir = Join-Path $RepoRoot "logs"
$statePath = Join-Path $logsDir "mcp-ops-monitor-state.json"
$logPath = Join-Path $logsDir "mcp-ops-monitor.log"
New-Item -Path $logsDir -ItemType Directory -Force | Out-Null

$endpoints = @(
    @{ Name = "gateway"; Url = "https://gateway.fusional.dev/health" },
    @{ Name = "bi"; Url = "https://bi.fusional.dev/health" },
    @{ Name = "api"; Url = "https://api.fusional.dev/health" },
    @{ Name = "content"; Url = "https://content.fusional.dev/health" },
    @{ Name = "intel"; Url = "https://intel.fusional.dev/health" }
)

function New-DefaultState {
    $obj = [ordered]@{
        endpointFailures = @{}
        remoteFailures = [ordered]@{
            cloudflaredDownCount = 0
        }
    }

    foreach ($ep in $endpoints) {
        $obj.endpointFailures[$ep.Name] = 0
    }

    return $obj
}

function Load-State {
    if (-not (Test-Path $statePath)) {
        return New-DefaultState
    }

    try {
        $raw = Get-Content -Path $statePath -Raw
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return New-DefaultState
        }

        $loaded = $raw | ConvertFrom-Json -AsHashtable
        if (-not $loaded.ContainsKey("endpointFailures") -or -not $loaded.ContainsKey("remoteFailures")) {
            return New-DefaultState
        }

        foreach ($ep in $endpoints) {
            if (-not $loaded.endpointFailures.ContainsKey($ep.Name)) {
                $loaded.endpointFailures[$ep.Name] = 0
            }
        }

        if (-not $loaded.remoteFailures.ContainsKey("cloudflaredDownCount")) {
            $loaded.remoteFailures.cloudflaredDownCount = 0
        }

        return $loaded
    }
    catch {
        return New-DefaultState
    }
}

function Save-State {
    param([hashtable]$State)

    $json = $State | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($statePath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function Test-HealthUrl {
    param(
        [string]$Url,
        [int]$TimeoutSec
    )

    Add-Type -AssemblyName System.Net.Http
    $handler = New-Object System.Net.Http.HttpClientHandler
    $client = New-Object System.Net.Http.HttpClient($handler)
    $client.Timeout = [TimeSpan]::FromSeconds($TimeoutSec)

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = $client.GetAsync($Url).GetAwaiter().GetResult()
        $stopwatch.Stop()
        [PSCustomObject]@{
            Ok = $response.IsSuccessStatusCode
            StatusCode = [int]$response.StatusCode
            LatencyMs = [int]$stopwatch.ElapsedMilliseconds
            Error = ""
        }
    }
    catch {
        $stopwatch.Stop()
        [PSCustomObject]@{
            Ok = $false
            StatusCode = 0
            LatencyMs = [int]$stopwatch.ElapsedMilliseconds
            Error = $_.Exception.Message
        }
    }
    finally {
        $client.Dispose()
        $handler.Dispose()
    }
}

function Get-RemoteHostSignals {
    param([string]$Alias)

    # Single SSH call: mem line, disk line, cloudflared check — separated by "---"
    $remoteCmd = 'free -m | grep Mem:; echo "---"; df -P / | tail -1; echo "---"; pgrep -f cloudflared >/dev/null && echo 1 || echo 0'
    $rawLines = ssh $Alias $remoteCmd 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $rawLines) {
        return [PSCustomObject]@{
            Ok = $false
            Error = "remote host check failed (single-call)"
            MemoryPct = -1
            DiskPct = -1
            CloudflaredUp = $false
        }
    }

    $sections = ($rawLines -join "`n") -split '---'
    if ($sections.Count -lt 3) {
        return [PSCustomObject]@{
            Ok = $false
            Error = "unable to parse remote host output (expected 3 sections, got $($sections.Count))"
            MemoryPct = -1
            DiskPct = -1
            CloudflaredUp = $false
        }
    }

    $memLine  = $sections[0].Trim()
    $diskLine = $sections[1].Trim()
    $cloudRaw = $sections[2].Trim()

    $memParts = ($memLine -split '\s+' | Where-Object { $_ -ne "" })
    if ($memParts.Count -lt 3) {
        return [PSCustomObject]@{
            Ok = $false
            Error = "unable to parse remote memory data"
            MemoryPct = -1
            DiskPct = -1
            CloudflaredUp = $false
        }
    }
    $memTotal = [double]$memParts[1]
    $memUsed  = [double]$memParts[2]
    $mem = if ($memTotal -gt 0) { [int][Math]::Round(($memUsed / $memTotal) * 100) } else { -1 }

    $diskParts = ($diskLine -split '\s+' | Where-Object { $_ -ne "" })
    if ($diskParts.Count -lt 5) {
        return [PSCustomObject]@{
            Ok = $false
            Error = "unable to parse remote disk data"
            MemoryPct = $mem
            DiskPct = -1
            CloudflaredUp = $false
        }
    }
    $disk  = [int]([string]$diskParts[4]).TrimEnd('%')
    $cloud = $cloudRaw -eq "1"

    [PSCustomObject]@{
        Ok = $true
        Error = ""
        MemoryPct = $mem
        DiskPct = $disk
        CloudflaredUp = $cloud
    }
}

$state = Load-State
$severityRank = 0
$reasons = New-Object System.Collections.Generic.List[string]
$results = New-Object System.Collections.Generic.List[object]

foreach ($ep in $endpoints) {
    $probe = Test-HealthUrl -Url $ep.Url -TimeoutSec $HttpTimeoutSec

    if ($probe.Ok) {
        $state.endpointFailures[$ep.Name] = 0
    }
    else {
        $state.endpointFailures[$ep.Name] = [int]$state.endpointFailures[$ep.Name] + 1
    }

    $failCount = [int]$state.endpointFailures[$ep.Name]

    if (-not $probe.Ok -and $failCount -ge $P1ConsecutiveDown) {
        $severityRank = [Math]::Max($severityRank, 2)
        $reasons.Add("P1 endpoint down: $($ep.Name) failCount=$failCount")
    }
    elseif (-not $probe.Ok -and $failCount -ge $P2ConsecutiveDown) {
        $severityRank = [Math]::Max($severityRank, 1)
        $reasons.Add("P2 endpoint unstable: $($ep.Name) failCount=$failCount")
    }

    if ($probe.Ok -and $probe.LatencyMs -ge $P1HealthLatencyMs) {
        $severityRank = [Math]::Max($severityRank, 2)
        $reasons.Add("P1 latency: $($ep.Name) latencyMs=$($probe.LatencyMs)")
    }
    elseif ($probe.Ok -and $probe.LatencyMs -ge $P2HealthLatencyMs) {
        $severityRank = [Math]::Max($severityRank, 1)
        $reasons.Add("P2 latency: $($ep.Name) latencyMs=$($probe.LatencyMs)")
    }

    $results.Add([PSCustomObject]@{
        name = $ep.Name
        url = $ep.Url
        ok = $probe.Ok
        statusCode = $probe.StatusCode
        latencyMs = $probe.LatencyMs
        failCount = $failCount
        error = $probe.Error
    })
}

$remoteSignals = $null
if (-not $SkipRemoteHostChecks) {
    $remoteSignals = Get-RemoteHostSignals -Alias $RemoteAlias

    if (-not $remoteSignals.Ok) {
        $severityRank = [Math]::Max($severityRank, 1)
        $reasons.Add("P2 remote checks failed: $($remoteSignals.Error)")
    }
    else {
        if ($remoteSignals.CloudflaredUp) {
            $state.remoteFailures.cloudflaredDownCount = 0
        }
        else {
            $state.remoteFailures.cloudflaredDownCount = [int]$state.remoteFailures.cloudflaredDownCount + 1
        }

        $cloudDownCount = [int]$state.remoteFailures.cloudflaredDownCount

        if (-not $remoteSignals.CloudflaredUp -and $cloudDownCount -ge 2) {
            $severityRank = [Math]::Max($severityRank, 2)
            $reasons.Add("P1 cloudflared down count=$cloudDownCount")
        }
        elseif (-not $remoteSignals.CloudflaredUp) {
            $severityRank = [Math]::Max($severityRank, 1)
            $reasons.Add("P2 cloudflared down first detection")
        }

        if ($remoteSignals.MemoryPct -ge $P1MemoryPct) {
            $severityRank = [Math]::Max($severityRank, 2)
            $reasons.Add("P1 memory pressure: $($remoteSignals.MemoryPct)%")
        }
        elseif ($remoteSignals.MemoryPct -ge $P2MemoryPct) {
            $severityRank = [Math]::Max($severityRank, 1)
            $reasons.Add("P2 memory pressure: $($remoteSignals.MemoryPct)%")
        }

        if ($remoteSignals.DiskPct -ge $P1DiskPct) {
            $severityRank = [Math]::Max($severityRank, 2)
            $reasons.Add("P1 disk pressure: $($remoteSignals.DiskPct)%")
        }
        elseif ($remoteSignals.DiskPct -ge $P2DiskPct) {
            $severityRank = [Math]::Max($severityRank, 1)
            $reasons.Add("P2 disk pressure: $($remoteSignals.DiskPct)%")
        }
    }
}

$severity = switch ($severityRank) {
    2 { "P1" }
    1 { "P2" }
    default { "OK" }
}

if ($remoteSignals) {
    $remoteEntry = @{
        checked = $true
        ok = $remoteSignals.Ok
        memoryPct = $remoteSignals.MemoryPct
        diskPct = $remoteSignals.DiskPct
        cloudflaredUp = $remoteSignals.CloudflaredUp
        error = $remoteSignals.Error
        cloudflaredDownCount = [int]$state.remoteFailures.cloudflaredDownCount
    }
}
else {
    $remoteEntry = @{ checked = $false }
}

$reasonsArray = @($reasons | ForEach-Object { [string]$_ })
$endpointsArray = @($results | ForEach-Object { $_ })

$entry = @{
    timestampUtc = (Get-Date).ToUniversalTime().ToString("o")
    severity = $severity
    reasons = $reasonsArray
    endpoints = $endpointsArray
    remote = $remoteEntry
}

Save-State -State $state
$line = $entry | ConvertTo-Json -Depth 10 -Compress
Add-Content -Path $logPath -Value $line

if (-not $Quiet) {
    Write-Host "[$severity] monitor-mcp-stack"
    foreach ($ep in $results) {
        $status = if ($ep.ok) { "OK" } else { "DOWN" }
        Write-Host ("  {0,-8} {1,-4} code={2} latencyMs={3} failCount={4}" -f $ep.name, $status, $ep.statusCode, $ep.latencyMs, $ep.failCount)
    }

    if ($remoteSignals) {
        if ($remoteSignals.Ok) {
            Write-Host ("  remote   mem={0}% disk={1}% cloudflared={2}" -f $remoteSignals.MemoryPct, $remoteSignals.DiskPct, $remoteSignals.CloudflaredUp)
        }
        else {
            Write-Host ("  remote   check failed: {0}" -f $remoteSignals.Error)
        }
    }

    if ($reasons.Count -gt 0) {
        Write-Host "  reasons:"
        foreach ($r in $reasons) {
            Write-Host "   - $r"
        }
    }

    Write-Host ("  log: {0}" -f $logPath)
}

switch ($severity) {
    "P1" { exit 2 }
    "P2" { exit 1 }
    default { exit 0 }
}
