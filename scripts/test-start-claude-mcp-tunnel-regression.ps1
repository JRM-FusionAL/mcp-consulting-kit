Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$targetScript = Join-Path $PSScriptRoot "start-claude-mcp-tunnel.ps1"
if (-not (Test-Path $targetScript)) {
    throw "Target script not found: $targetScript"
}

$content = Get-Content -Path $targetScript -Raw

function Assert-ContainsPattern {
    param(
        [string]$Text,
        [string]$Pattern,
        [string]$Message
    )

    if ($Text -notmatch $Pattern) {
        throw $Message
    }
}

Assert-ContainsPattern -Text $content -Pattern 'return\s+@\(\$inactive\)' -Message 'Regression guard failed: Get-InactiveTunnelPorts must return an array with return @($inactive).'
Assert-ContainsPattern -Text $content -Pattern '\$stillMissing\s*=\s*@\(Get-InactiveTunnelPorts\s+-Ports\s+\$TunnelPorts\)' -Message "Regression guard failed: stillMissing must wrap Get-InactiveTunnelPorts in @(...)."
Assert-ContainsPattern -Text $content -Pattern '\$afterPrimaryMissing\s*=\s*@\(Get-InactiveTunnelPorts\s+-Ports\s+\$TunnelPorts\)' -Message "Regression guard failed: afterPrimaryMissing must wrap Get-InactiveTunnelPorts in @(...)."

$stillMissingMatches = [regex]::Matches($content, '\$stillMissing\s*=\s*@\(Get-InactiveTunnelPorts\s+-Ports\s+\$TunnelPorts\)')
if ($stillMissingMatches.Count -lt 2) {
    throw "Regression guard failed: expected stillMissing array coercion at both primary and fallback loops. Found $($stillMissingMatches.Count)."
}

function Get-InactiveTunnelPorts-Probe {
    param(
        [int[]]$Ports,
        [int[]]$Listening
    )

    $inactive = @()
    foreach ($port in $Ports) {
        if ($Listening -notcontains $port) {
            $inactive += $port
        }
    }

    return @($inactive)
}

$allPorts = @(18009, 18101, 18102)
$singleMissing = @(Get-InactiveTunnelPorts-Probe -Ports $allPorts -Listening @(18009, 18102))
$multiMissing = @(Get-InactiveTunnelPorts-Probe -Ports $allPorts -Listening @(18009))
$noneMissing = @(Get-InactiveTunnelPorts-Probe -Ports $allPorts -Listening $allPorts)

if ($singleMissing.Count -ne 1) {
    throw "Regression guard failed: single missing port must still return array count 1."
}
if ($multiMissing.Count -ne 2) {
    throw "Regression guard failed: two missing ports must return array count 2."
}
if ($noneMissing.Count -ne 0) {
    throw "Regression guard failed: no missing ports must return array count 0."
}

Write-Host "PASS: tunnel bootstrap scalar/array regression checks succeeded." -ForegroundColor Green
