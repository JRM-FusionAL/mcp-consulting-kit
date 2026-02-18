$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$candidatePythonPaths = @()

if ($env:VIRTUAL_ENV) {
    $candidatePythonPaths += (Join-Path $env:VIRTUAL_ENV "Scripts/python.exe")
}

$candidatePythonPaths += (Join-Path $repoRoot ".venv/Scripts/python.exe")
$candidatePythonPaths += (Join-Path $HOME ".venv/Scripts/python.exe")

$pythonCmd = $null
foreach ($candidate in $candidatePythonPaths) {
    if (Test-Path $candidate) {
        $pythonCmd = $candidate
        break
    }
}

if (-not $pythonCmd) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python executable not found. Activate a virtual environment or install Python."
    }
    $pythonCmd = $python.Source
}

$showcaseServers = Join-Path $repoRoot "showcase-servers"
$biDir = Join-Path $showcaseServers "business-intelligence-mcp"
if (-not (Test-Path $biDir)) {
    throw "business-intelligence-mcp directory not found under showcase-servers."
}

$commonTest = Join-Path $showcaseServers "common/test_security_common.py"
$biTest = Join-Path $biDir "test_security.py"

& $pythonCmd -m pytest -q $commonTest $biTest
exit $LASTEXITCODE
