param(
    [switch]$UseTunnelPorts,
    [switch]$AllowClaudeRunning,
    [switch]$BackupOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Set-ObjectProperty {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)]$Value
    )

    if ($Object.PSObject.Properties[$Name]) {
        $Object.$Name = $Value
    }
    else {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

function Ensure-ObjectProperty {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (-not $Object.PSObject.Properties[$Name] -or $null -eq $Object.$Name) {
        $child = [pscustomobject]@{}
        Set-ObjectProperty -Object $Object -Name $Name -Value $child
        return $child
    }

    return $Object.$Name
}

function New-McpRemoteEntry {
    param([Parameter(Mandatory = $true)][string]$Url)

    return [pscustomobject]@{
        command = "npx"
        args = @("-y", "mcp-remote", $Url, "--allow-http")
    }
}

$configPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"

if (-not (Test-Path $configPath)) {
    throw "Claude config not found at: $configPath"
}

$claudeProcesses = Get-Process -Name "claude" -ErrorAction SilentlyContinue
if ($claudeProcesses -and -not $AllowClaudeRunning) {
    throw "Claude Desktop is running. Quit Claude completely, then rerun this script. Use -AllowClaudeRunning only if you know what you are doing."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$configPath.bak-$timestamp"
Copy-Item -Path $configPath -Destination $backupPath -Force

Write-Host "Backup created: $backupPath"

if ($BackupOnly) {
    Write-Host "Backup-only mode complete."
    exit 0
}

$raw = Get-Content -Path $configPath -Raw

if ([string]::IsNullOrWhiteSpace($raw)) {
    $config = [pscustomobject]@{}
}
else {
    try {
        $config = $raw | ConvertFrom-Json
    }
    catch {
        throw "Existing Claude config is not valid JSON. Restore from backup and retry."
    }
}

$mcpServers = Ensure-ObjectProperty -Object $config -Name "mcpServers"

$existingGithubToken = "REPLACE_WITH_NEW_GITHUB_TOKEN"
if ($mcpServers.PSObject.Properties["github-safe"] -and
    $mcpServers."github-safe".PSObject.Properties["env"] -and
    $mcpServers."github-safe".env.PSObject.Properties["GITHUB_TOKEN"] -and
    -not [string]::IsNullOrWhiteSpace($mcpServers."github-safe".env.GITHUB_TOKEN)) {
    $existingGithubToken = [string]$mcpServers."github-safe".env.GITHUB_TOKEN
}

$existingNotionHeaders = ""
if ($mcpServers.PSObject.Properties["notion-mcp"] -and
    $mcpServers."notion-mcp".PSObject.Properties["env"] -and
    $mcpServers."notion-mcp".env.PSObject.Properties["OPENAPI_MCP_HEADERS"] -and
    -not [string]::IsNullOrWhiteSpace($mcpServers."notion-mcp".env.OPENAPI_MCP_HEADERS)) {
    $existingNotionHeaders = [string]$mcpServers."notion-mcp".env.OPENAPI_MCP_HEADERS
}

if ($UseTunnelPorts) {
    $fusionUrl = "http://localhost:18009/mcp/"
    $biUrl = "http://localhost:18101/mcp/"
    $apiUrl = "http://localhost:18102/mcp/"
    $contentUrl = "http://localhost:18103/mcp/"
}
else {
    $fusionUrl = "http://localhost:8009/mcp/"
    $biUrl = "http://localhost:8101/mcp/"
    $apiUrl = "http://localhost:8102/mcp/"
    $contentUrl = "http://localhost:8103/mcp/"
}

$githubSafe = [pscustomobject]@{
    command = "C:\\Users\\puddi\\Projects\\github-mcp-safe\\dist\\github-mcp-safe-windows.exe"
    env = [pscustomobject]@{
        GITHUB_TOKEN = $existingGithubToken
    }
}

$notionMcp = [pscustomobject]@{
    command = "npx"
    args = @("-y", "@notionhq/notion-mcp-server")
    env = [pscustomobject]@{
        OPENAPI_MCP_HEADERS = $existingNotionHeaders
    }
}

Set-ObjectProperty -Object $mcpServers -Name "github-safe" -Value $githubSafe
Set-ObjectProperty -Object $mcpServers -Name "notion-mcp" -Value $notionMcp
Set-ObjectProperty -Object $mcpServers -Name "business-intelligence-mcp" -Value (New-McpRemoteEntry -Url $biUrl)
Set-ObjectProperty -Object $mcpServers -Name "api-integration-hub" -Value (New-McpRemoteEntry -Url $apiUrl)
Set-ObjectProperty -Object $mcpServers -Name "content-automation-mcp" -Value (New-McpRemoteEntry -Url $contentUrl)
Set-ObjectProperty -Object $mcpServers -Name "fusional-mcp" -Value (New-McpRemoteEntry -Url $fusionUrl)

if (-not $config.PSObject.Properties["isDxtAutoUpdatesEnabled"]) {
    Set-ObjectProperty -Object $config -Name "isDxtAutoUpdatesEnabled" -Value $true
}

$json = $config | ConvertTo-Json -Depth 20

# Write UTF-8 without BOM. BOM can break some JSON loaders.
[System.IO.File]::WriteAllText($configPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

$reloaded = Get-Content -Path $configPath -Raw
try {
    $validated = $reloaded | ConvertFrom-Json
}
catch {
    throw "JSON validation failed after write. Restore backup: $backupPath"
}

if (-not $validated.PSObject.Properties["mcpServers"]) {
    throw "Validation failed: mcpServers property missing. Restore backup: $backupPath"
}

$expectedUrls = @($fusionUrl, $biUrl, $apiUrl, $contentUrl)
$actualArgs = @()
foreach ($serverName in @("fusional-mcp", "business-intelligence-mcp", "api-integration-hub", "content-automation-mcp")) {
    if ($validated.mcpServers.PSObject.Properties[$serverName] -and $validated.mcpServers.$serverName.PSObject.Properties["args"]) {
        $actualArgs += ($validated.mcpServers.$serverName.args -join " ")
    }
}

foreach ($url in $expectedUrls) {
    if (-not ($actualArgs | Where-Object { $_ -like "*$url*" })) {
        throw "Validation failed: expected URL not found in MCP args: $url"
    }
}

$firstBytes = [System.IO.File]::ReadAllBytes($configPath) | Select-Object -First 3
$hasBom = ($firstBytes.Count -eq 3 -and $firstBytes[0] -eq 0xEF -and $firstBytes[1] -eq 0xBB -and $firstBytes[2] -eq 0xBF)
if ($hasBom) {
    throw "Validation failed: file still has UTF-8 BOM. Restore backup: $backupPath"
}

Write-Host "Claude MCP config hardened successfully."
Write-Host "Config path: $configPath"
Write-Host "Mode: $([string]::Join('', @($(if ($UseTunnelPorts) { 'tunnel ports (18xxx)' } else { 'local ports (8xxx)' }))))"
Write-Host "No BOM: true"

if ($existingGithubToken -eq "REPLACE_WITH_NEW_GITHUB_TOKEN") {
    Write-Warning "github-safe still uses placeholder token. Replace GITHUB_TOKEN before using that server."
}

if ([string]::IsNullOrWhiteSpace($existingNotionHeaders)) {
    Write-Warning "notion-mcp OPENAPI_MCP_HEADERS is empty. Add your Notion auth header if needed."
}
