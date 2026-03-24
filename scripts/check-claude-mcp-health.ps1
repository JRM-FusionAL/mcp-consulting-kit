param(
    [switch]$UseTunnelPorts,
    [switch]$Quiet
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
        [int]$Port
    )

    $url = "http://localhost:$Port/health"
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 5 -UseBasicParsing
        [PSCustomObject]@{
            Service = $Name
            Port = $Port
            StatusCode = [int]$response.StatusCode
            Healthy = ([int]$response.StatusCode -eq 200)
            Url = $url
        }
    }
    catch {
        [PSCustomObject]@{
            Service = $Name
            Port = $Port
            StatusCode = 0
            Healthy = $false
            Url = $url
        }
    }
}

$results = foreach ($target in $targets) {
    Get-HealthStatus -Name $target.Name -Port $target.Port
}

if (-not $Quiet) {
    $results | Format-Table -AutoSize
}

$failed = $results | Where-Object { -not $_.Healthy }
if ($failed) {
    $failedNames = ($failed | Select-Object -ExpandProperty Service) -join ", "
    if ($UseTunnelPorts) {
        throw "Health check failed for: $failedNames. Tunnel mode checks localhost:18xxx ports; run start-claude-mcp-tunnel.ps1 first (or pass -ForceRestart)."
    }

    throw "Health check failed for: $failedNames. Local mode checks localhost:8xxx ports; ensure services are running (launch-servers.ps1)."
}

$modeLabel = if ($UseTunnelPorts) { "tunnel (18xxx)" } else { "local (8xxx)" }
if (-not $Quiet) {
    Write-Host "All MCP services healthy. Mode: $modeLabel"
}
