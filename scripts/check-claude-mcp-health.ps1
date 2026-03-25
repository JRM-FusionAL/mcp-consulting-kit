param(
    [switch]$UseTunnelPorts,
    [switch]$Quiet,
    [ValidateRange(1, 10)]
    [int]$Attempts = 3,
    [ValidateRange(100, 5000)]
    [int]$RetryDelayMs = 500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($UseTunnelPorts) {
    $targets = @(
        @{ Name = "FusionAL"; Port = 18009 },
        @{ Name = "Business Intelligence"; Port = 18101 },
        @{ Name = "API Integration"; Port = 18102 },
        @{ Name = "Content Automation"; Port = 18103 },
        @{ Name = "Intelligence"; Port = 18104 }
    )
}
else {
    $targets = @(
        @{ Name = "FusionAL"; Port = 8009 },
        @{ Name = "Business Intelligence"; Port = 8101 },
        @{ Name = "API Integration"; Port = 8102 },
        @{ Name = "Content Automation"; Port = 8103 },
        @{ Name = "Intelligence"; Port = 8104 }
    )
}

function Get-HealthStatus {
    param(
        [string]$Name,
        [int]$Port,
        [int]$Attempts,
        [int]$RetryDelayMs
    )

    $url = "http://localhost:$Port/health"
    $lastStatusCode = 0
    $lastError = ""

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5 -UseBasicParsing
            $statusCode = [int]$response.StatusCode
            if ($statusCode -eq 200) {
                return [PSCustomObject]@{
                    Service = $Name
                    Port = $Port
                    StatusCode = $statusCode
                    Healthy = $true
                    Url = $url
                    AttemptsUsed = $i
                    LastError = ""
                }
            }

            $lastStatusCode = $statusCode
            $lastError = "HTTP $statusCode"
        }
        catch {
            if ($null -ne $_.Exception.Response -and $null -ne $_.Exception.Response.StatusCode) {
                $lastStatusCode = [int]$_.Exception.Response.StatusCode.value__
                $lastError = "HTTP $lastStatusCode"
            }
            else {
                $lastStatusCode = 0
                $lastError = $_.Exception.Message
            }
        }

        if ($i -lt $Attempts) {
            Start-Sleep -Milliseconds $RetryDelayMs
        }
    }

    return [PSCustomObject]@{
        Service = $Name
        Port = $Port
        StatusCode = $lastStatusCode
        Healthy = $false
        Url = $url
        AttemptsUsed = $Attempts
        LastError = $lastError
    }
}

$results = foreach ($target in $targets) {
    Get-HealthStatus -Name $target.Name -Port $target.Port -Attempts $Attempts -RetryDelayMs $RetryDelayMs
}

if (-not $Quiet) {
    $results | Select-Object Service, Port, StatusCode, Healthy, AttemptsUsed, LastError, Url | Format-Table -AutoSize
}

$failed = $results | Where-Object { -not $_.Healthy }
if ($failed) {
    $failedDetails = ($failed | ForEach-Object {
        $reason = if ([string]::IsNullOrWhiteSpace($_.LastError)) { "unknown" } else { $_.LastError }
        "{0} (port {1}, status {2}, attempts {3}, reason: {4})" -f $_.Service, $_.Port, $_.StatusCode, $_.AttemptsUsed, $reason
    }) -join "; "

    if ($UseTunnelPorts) {
        throw "Health check failed after $Attempts attempt(s): $failedDetails. Tunnel mode checks localhost:18xxx ports; run start-claude-mcp-tunnel.ps1 first (or pass -ForceRestart)."
    }

    throw "Health check failed after $Attempts attempt(s): $failedDetails. Local mode checks localhost:8xxx ports; ensure services are running (launch-servers.ps1)."
}

$modeLabel = if ($UseTunnelPorts) { "tunnel (18xxx)" } else { "local (8xxx)" }
if (-not $Quiet) {
    Write-Host "All MCP services healthy. Mode: $modeLabel. Attempts per service: $Attempts"
}
