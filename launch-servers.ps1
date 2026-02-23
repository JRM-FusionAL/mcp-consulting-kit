# Launch all 3 MCP servers in separate PowerShell windows

$root = "C:\Users\puddi\Projects\mcp-consulting-kit\showcase-servers"

$servers = @(
    @{ dir = "business-intelligence-mcp";  port = 8101 },
    @{ dir = "api-integration-hub";        port = 8102 },
    @{ dir = "content-automation-mcp";     port = 8103 }
)

foreach ($server in $servers) {
    $path = Join-Path $root $server.dir
    $cmd = @"
cd '$path'
Get-Content .env | ForEach-Object {
    if (`$_ -match '^\s*#' -or `$_ -notmatch '=') { return }
    `$name, `$value = `$_ -split '=', 2
    [System.Environment]::SetEnvironmentVariable(`$name.Trim(), `$value.Trim())
}
Write-Host 'Starting $($server.dir) on port $($server.port)...' -ForegroundColor Cyan
uvicorn main:app --host 0.0.0.0 --port $($server.port) --reload
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
}

Write-Host "All 3 servers launching..." -ForegroundColor Green
Write-Host "  BI MCP:              http://localhost:8101/health"
Write-Host "  API Integration Hub: http://localhost:8102/health"
Write-Host "  Content Automation:  http://localhost:8103/health"
