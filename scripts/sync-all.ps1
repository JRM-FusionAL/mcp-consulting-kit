param(
    [string]$RemoteAlias = "t3610",
    [string]$RemoteBase = "/home/jrm_fusional/Projects",
    [switch]$RestartDocker,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repos = @(
    "mcp-consulting-kit",
    "FusionAL",
    "Christopher-AI"
)

$localBase = Resolve-Path (Join-Path $PSScriptRoot "..\..")

if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    throw "ssh command not found. Install OpenSSH client first."
}

if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
    throw "tar command not found. Install bsdtar/GNU tar first."
}

if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    throw "scp command not found. Install OpenSSH client first."
}

Write-Host ""
Write-Host "Sync plan"
Write-Host "  Local base : $($localBase.Path)"
Write-Host ("  Remote     : {0}:{1}" -f $RemoteAlias, $RemoteBase)
Write-Host "  Repos      : $($repos -join ', ')"
Write-Host "  Dry run    : $DryRun"
Write-Host ""

foreach ($repo in $repos) {
    $srcPath = Join-Path $localBase.Path $repo
    if (-not (Test-Path $srcPath)) {
        Write-Warning "Skipping missing repo: $srcPath"
        continue
    }

    Write-Host "[SYNC] $repo"

    if ($DryRun) {
        continue
    }

    ssh $RemoteAlias "mkdir -p '$RemoteBase/$repo'"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create remote directory for $repo"
    }

    $tmpArchive = Join-Path $env:TEMP ("sync-{0}-{1}.tar" -f $repo, [guid]::NewGuid().ToString("N"))

    $tarArgs = @(
        "-cf", $tmpArchive,
        "-C", $localBase.Path,
        "--exclude=.git",
        "--exclude=.venv",
        "--exclude=venv",
        "--exclude=node_modules",
        "--exclude=__pycache__",
        "--exclude=.pytest_cache",
        "--exclude=dist",
        "--exclude=build",
        $repo
    )

    & tar @tarArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create archive for $repo"
    }

    $remoteArchive = ("{0}:{1}/{2}.tar" -f $RemoteAlias, $RemoteBase, $repo)
    scp $tmpArchive $remoteArchive
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Force $tmpArchive -ErrorAction SilentlyContinue
        throw "Failed to upload archive for $repo"
    }

    ssh $RemoteAlias "tar -xf '$RemoteBase/$repo.tar' -C '$RemoteBase' ; rm -f '$RemoteBase/$repo.tar'"
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Force $tmpArchive -ErrorAction SilentlyContinue
        throw "Failed to extract archive for $repo"
    }

    Remove-Item -Force $tmpArchive -ErrorAction SilentlyContinue
}

if ($RestartDocker) {
    Write-Host ""
    Write-Host "[REMOTE] Refreshing docker services"

        $remoteCmd = "set -e; for port in 8101 8102 8103 8104; do lsof -ti:\${port} 2>/dev/null | xargs -r kill -9 2>/dev/null; done; if [ -f '$RemoteBase/mcp-consulting-kit/docker-compose.yaml' ]; then cd '$RemoteBase/mcp-consulting-kit'; if docker compose version >/dev/null 2>&1; then docker compose down --remove-orphans; docker compose up -d --build; else docker-compose down --remove-orphans; docker-compose up -d --build; fi; fi; if [ -f '$RemoteBase/FusionAL/compose.yaml' ]; then cd '$RemoteBase/FusionAL'; if docker compose version >/dev/null 2>&1; then docker compose down --remove-orphans; docker compose up -d --build; else docker-compose down --remove-orphans; docker-compose up -d --build; fi; fi"
        ssh $RemoteAlias "bash -lc \"$remoteCmd\""
        if ($LASTEXITCODE -ne 0) {
                throw "Remote docker refresh failed"
        }
}

Write-Host ""
Write-Host "Sync completed."
