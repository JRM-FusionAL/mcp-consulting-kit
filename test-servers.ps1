# Test all 3 MCP servers
# Usage: .\test-servers.ps1 -ApiKey "test-key-123"

param(
    [string]$ApiKey = "test-key-123"
)

$headers = @{
    "X-API-Key"    = $ApiKey
    "Content-Type" = "application/json"
}

function Test-Endpoint {
    param($label, $uri, $method = "GET", $body = $null)
    Write-Host "`n--- $label ---" -ForegroundColor Yellow
    try {
        if ($method -eq "GET") {
            $r = Invoke-RestMethod -Uri $uri -Method GET
        } else {
            $r = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body ($body | ConvertTo-Json) -ContentType "application/json"
        }
        $r | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Health checks (no auth needed)
Test-Endpoint "BI MCP Health"              "http://localhost:8101/health"
Test-Endpoint "API Hub Health"             "http://localhost:8102/health"
Test-Endpoint "Content Automation Health"  "http://localhost:8103/health"

# Business Intelligence MCP
Test-Endpoint "NL Query - top customers" "http://localhost:8101/nl-query" "POST" @{
    query       = "show me the top 10 customers by revenue"
    schema_hint = "customers(id, name, revenue)"
}

# Content Automation MCP
Test-Endpoint "Scrape Article" "http://localhost:8103/scrape/article" "POST" @{
    url = "https://example.com"
}

Test-Endpoint "Scrape Links" "http://localhost:8103/scrape/links" "POST" @{
    url = "https://example.com"
}

Test-Endpoint "Parse RSS" "http://localhost:8103/rss/parse" "POST" @{
    url   = "https://feeds.bbci.co.uk/news/rss.xml"
    limit = 5
}

Write-Host "`nDone." -ForegroundColor Green
