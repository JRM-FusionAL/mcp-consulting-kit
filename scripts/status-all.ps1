param(
    [string]$RemoteAlias = "t3610",
    [switch]$SkipRemote
)

$ErrorActionPreference = "Stop"

$corePorts = @(8101, 8102, 8103, 8104)
$fusionalPorts = @(8089, 8009)

function Test-Health {
    param(
        [string]$HostLabel,
        [string]$BaseHost
    )

    Write-Host ""
    Write-Host "[$HostLabel]"
    foreach ($p in $corePorts) {
        $url = "http://$BaseHost`:$p/health"
        try {
            $resp = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
                Write-Host ("  port {0}: OK" -f $p)
            } else {
                Write-Host ("  port {0}: HTTP {1}" -f $p, [int]$resp.StatusCode)
            }
        } catch {
            Write-Host ("  port {0}: DOWN" -f $p)
        }
    }

    $fusionalOk = $false
    foreach ($p in $fusionalPorts) {
        $url = "http://$BaseHost`:$p/health"
        try {
            $resp = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) {
                Write-Host ("  FusionAL: OK on port {0}" -f $p)
                $fusionalOk = $true
                break
            }
        } catch {
        }
    }

    if (-not $fusionalOk) {
        Write-Host "  FusionAL: DOWN (checked 8089 and 8009)"
    }
}

Test-Health -HostLabel "LOCAL" -BaseHost "127.0.0.1"

if (-not $SkipRemote) {
    Write-Host ""
    Write-Host "[REMOTE:$RemoteAlias]"
    $cmd = "echo -n '  port 8101: '; curl -fsS --max-time 5 http://127.0.0.1:8101/health >/dev/null 2>/dev/null && echo OK || echo DOWN; echo -n '  port 8102: '; curl -fsS --max-time 5 http://127.0.0.1:8102/health >/dev/null 2>/dev/null && echo OK || echo DOWN; echo -n '  port 8103: '; curl -fsS --max-time 5 http://127.0.0.1:8103/health >/dev/null 2>/dev/null && echo OK || echo DOWN; echo -n '  port 8104: '; curl -fsS --max-time 5 http://127.0.0.1:8104/health >/dev/null 2>/dev/null && echo OK || echo DOWN; if curl -fsS --max-time 5 http://127.0.0.1:8089/health >/dev/null 2>/dev/null; then echo '  FusionAL: OK on port 8089'; elif curl -fsS --max-time 5 http://127.0.0.1:8009/health >/dev/null 2>/dev/null; then echo '  FusionAL: OK on port 8009'; else echo '  FusionAL: DOWN (checked 8089 and 8009)'; fi"
    ssh $RemoteAlias "bash -lc \"$cmd\""
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  remote check command failed"
    }
}
