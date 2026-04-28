param(
    # Directory to open Claude Code in (defaults to Projects root)
    [string]$WorkDir = "C:\Users\puddi\Projects"
)

$claudeCodeExe = "$env:LOCALAPPDATA\Microsoft\WinGet\Links\claude.exe"

if (-not (Test-Path $claudeCodeExe)) {
    # Fallback: find claude on PATH
    $claudeCodeExe = (Get-Command "claude" -ErrorAction SilentlyContinue)?.Source
}

if (-not $claudeCodeExe) {
    Write-Warning "claude.exe not found. Install via: winget install Anthropic.Claude"
    exit 1
}

# Prefer Windows Terminal; fall back to PowerShell
$wt = (Get-Command "wt" -ErrorAction SilentlyContinue)?.Source

if ($wt) {
    Start-Process $wt -ArgumentList "new-tab", "--startingDirectory", "`"$WorkDir`"", "pwsh", "-NoExit", "-Command", "`"& '$claudeCodeExe'`""
} else {
    Start-Process "pwsh" -ArgumentList "-NoExit", "-Command", "Set-Location '$WorkDir'; & '$claudeCodeExe'"
}

Write-Host "Claude Code launched in $WorkDir" -ForegroundColor Green
