Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$targets = @(
    @{ Name = "FusionAL"; Port = 18009 },
    @{ Name = "Business Intelligence"; Port = 18101 },
    @{ Name = "API Integration"; Port = 18102 },
    @{ Name = "Content Automation"; Port = 18103 }
)

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

$results | Format-Table -AutoSize

if ($results.Healthy -contains $false) {
    throw "One or more MCP services failed health checks."
}

Write-Host "All tunneled MCP services are healthy."
