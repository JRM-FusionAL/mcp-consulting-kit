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
        @{ Name = "Content Automation"; Port = 18103 }
    )
}
else {
    $targets = @(
        @{ Name = "FusionAL"; Port = 8009 },
        @{ Name = "Business Intelligence"; Port = 8101 },
        @{ Name = "API Integration"; Port = 8102 },
        @{ Name = "Content Automation"; Port = 8103 }
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
    throw "Health check failed for: $failedNames"
}

$modeLabel = if ($UseTunnelPorts) { "tunnel (18xxx)" } else { "local (8xxx)" }
if (-not $Quiet) {
    Write-Host "All MCP services healthy. Mode: $modeLabel"
}
