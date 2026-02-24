# Launch all servers: 3 consulting-kit showcase servers + FusionAL execution engine
# Usage: .\launch-servers.ps1

$showcaseRoot = "C:\Users\puddi\Projects\mcp-consulting-kit\showcase-servers"
$fusionalRoot = "C:\Users\puddi\projects\FusionAL\core"

$servers = @(
    @{ name = "Business Intelligence MCP";  dir = "$showcaseRoot\business-intelligence-mcp";  port = 8101 },
    @{ name = "API Integration Hub";         dir = "$showcaseRoot\api-integration-hub";         port = 8102 },
    @{ name = "Content Automation MCP";      dir = "$showcaseRoot\content-automation-mcp";      port = 8103 },
    @{ name = "FusionAL Execution Engine";   dir = $fusionalRoot;                               port = 8009 }
)

foreach ($server in $servers) {
    $path = $server.dir
    $port = $server.port
    $name = $server.name

    $cmd = @"
cd '$path'
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if (`$_ -match '^\s*#' -or `$_ -notmatch '=') { return }
        `$parts = `$_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable(`$parts[0].Trim(), `$parts[1].Trim())
    }
}
Write-Host 'Starting $name on port $port...' -ForegroundColor Cyan
uvicorn main:app --host 0.0.0.0 --port $port --reload
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "All servers launching..." -ForegroundColor Green
Write-Host "  Business Intelligence MCP : http://localhost:8101/health"
Write-Host "  API Integration Hub       : http://localhost:8102/health"
Write-Host "  Content Automation MCP    : http://localhost:8103/health"
Write-Host "  FusionAL Execution Engine : http://localhost:8009/health"
Write-Host ""
Write-Host "FusionAL catalog (all servers): http://localhost:8009/catalog"
