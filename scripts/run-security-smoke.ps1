$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$candidatePythonPaths = @()

if ($env:VIRTUAL_ENV) {
    $candidatePythonPaths += (Join-Path $env:VIRTUAL_ENV "Scripts/python.exe")
}

$candidatePythonPaths += (Join-Path $repoRoot ".venv/Scripts/python.exe")
$candidatePythonPaths += (Join-Path (Split-Path -Parent $repoRoot) ".venv/Scripts/python.exe")
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
$biRequirements = Join-Path $biDir "requirements.txt"

# Local test imports expect a package name (showcase_servers) that is created in Docker builds.
# Create a temporary shim package so local smoke runs mirror container import behavior.
$tmpPkgRoot = Join-Path $env:TEMP "mcpk_shim_pkg"
$pkgDir = Join-Path $tmpPkgRoot "showcase_servers"
$commonSrc = Join-Path $showcaseServers "common"
$oldPythonPath = $env:PYTHONPATH

if (Test-Path $tmpPkgRoot) {
    Remove-Item -Recurse -Force $tmpPkgRoot
}

New-Item -ItemType Directory -Path $pkgDir | Out-Null
New-Item -ItemType File -Path (Join-Path $pkgDir "__init__.py") | Out-Null
Copy-Item -Path $commonSrc -Destination (Join-Path $pkgDir "common") -Recurse -Force

$env:PYTHONPATH = "$tmpPkgRoot;$commonSrc;$biDir"

try {
    Write-Host "Using Python: $pythonCmd"
    if (Test-Path $biRequirements) {
        & $pythonCmd -m pip install -r $biRequirements --disable-pip-version-check
    }

    & $pythonCmd -m pytest -q $commonTest $biTest
    exit $LASTEXITCODE
}
finally {
    if (Test-Path $tmpPkgRoot) {
        Remove-Item -Recurse -Force $tmpPkgRoot
    }

    if ([string]::IsNullOrEmpty($oldPythonPath)) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $oldPythonPath
    }
}
