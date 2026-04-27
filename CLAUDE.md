# CLAUDE.md — MCP Consulting Kit

This file is the authoritative AI assistant guide for the `mcp-consulting-kit` repository.
Read this before making any changes.

## What This Repo Is

A production-grade collection of five MCP (Model Context Protocol) servers plus a consulting
framework. It is the **server layer** that pairs with the FusionAL governance gateway
(`fusional` repo) and the Christopher voice assistant (`christopher-ai` repo).

Primary audience: consulting clients who need done-for-you MCP deployments.
Primary deployment target: `t3610` — a remote Linux server accessed via SSH.

---

## Port Map

| Service | Port | Container name |
|---------|------|----------------|
| Business Intelligence MCP | 8101 | `business-intelligence-mcp` |
| API Integration Hub | 8102 | `api-integration-hub` |
| Content Automation MCP | 8103 | `content-automation-mcp` |
| Intelligence MCP | 8104 | `intelligence-mcp` |
| FusionAL Execution Engine | 8009 | (runs from `fusional` repo) |
| GitHub MCP Safe | 8105 | `github-mcp-safe` |
| Nginx reverse proxy | 8088 | — |

Health check pattern for every server: `GET /health` → `{"status": "ok"}`

---

## Directory Structure

```
mcp-consulting-kit/
├── showcase-servers/          # The five MCP server implementations
│   ├── business-intelligence-mcp/  # Natural language → SQL (port 8101)
│   ├── api-integration-hub/        # Slack, GitHub, Stripe (port 8102)
│   ├── content-automation-mcp/     # Scraping, RSS, links (port 8103)
│   ├── github-mcp-safe/            # Safe GitHub operations (port 8105)
│   ├── social-poster-mcp/          # Social media posting
│   └── common/                     # Shared modules (security, audit, tracing)
│       ├── security.py             # API key auth, rate limiting, CORS
│       ├── audit.py                # Tool-call audit logging
│       └── tracing.py              # OpenTelemetry tracing
├── app/                       # Vite + React frontend dashboard
│   ├── src/                   # React source
│   ├── dist/                  # Build output (served by nginx)
│   └── package.json
├── bundles/                   # Deployment bundles for clients
├── consulting-materials/      # Client-facing proposal templates, SOWs
├── deploy/                    # Deployment configs and scripts
├── docs/                      # Runbooks and guides (see below)
├── nginx-config-fix/          # Nginx config patches
├── scripts/                   # PowerShell + Bash automation scripts
├── intelligence_mcp.py        # Intelligence MCP server entry point
├── get_intelligence.py        # Intelligence data fetching module
├── launch.py                  # Cross-platform Python launcher
├── launch.sh                  # Linux/macOS launcher
├── launch-all-servers.bat     # Windows batch launcher
├── launch-servers.ps1         # PowerShell launcher
├── docker-compose.yaml        # Main Docker Compose (all servers)
├── docker-compose.fusional.yaml
├── docker-compose.proxy.yaml  # Nginx proxy compose
├── docker-compose.cloudflare.yaml
├── nginx.conf                 # Nginx reverse proxy config
├── Dockerfile.intelligence    # Intelligence MCP Dockerfile
├── test-servers.ps1           # Server health test suite
├── .bandit                    # Bandit security scanner config
└── .trivyignore               # Trivy CVE scanner ignore list
```

### Each showcase server follows this layout:
```
showcase-servers/<server-name>/
├── Dockerfile
├── <server_name>.py     # FastMCP server implementation
├── requirements.txt
├── .env.example
└── .env                 # NOT committed — copy from .env.example
```

### `showcase-servers/common/` — Shared security modules

This directory is a **cross-repo dependency**. The `fusional` gateway imports from it at
runtime via dynamic path resolution. Do not rename or restructure it without updating
`fusional/core/main.py`'s `_SECURITY_CANDIDATES` list.

---

## How to Run

### Local development (no Docker)

```bash
# Install all deps (one-time)
pip3 install fastapi uvicorn[standard] python-dotenv pydantic requests \
             beautifulsoup4 feedparser lxml sqlalchemy "mcp[cli]"

# Copy and fill env files
cp showcase-servers/business-intelligence-mcp/.env.example showcase-servers/business-intelligence-mcp/.env
cp showcase-servers/api-integration-hub/.env.example showcase-servers/api-integration-hub/.env
cp showcase-servers/content-automation-mcp/.env.example showcase-servers/content-automation-mcp/.env

# Launch all servers
./launch.sh                  # Linux/macOS
python3 launch.py            # Any platform
launch-all-servers.bat       # Windows CMD
```

### Docker (recommended for production)

```bash
# Start all MCP servers
docker compose up -d

# Start with nginx proxy
docker compose -f docker-compose.yaml -f docker-compose.proxy.yaml up -d

# Verify
curl http://localhost:8101/health
curl http://localhost:8102/health
curl http://localhost:8103/health
curl http://localhost:8104/health
```

### Verify through nginx proxy

```bash
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/healthz
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/bi/
```

---

## Environment Variables

Each server reads from its own `.env` file. Common variables across all servers:

| Variable | Description |
|----------|-------------|
| `API_KEY` | Required header value for `X-API-Key` auth |
| `API_KEYS` | Comma-separated list for zero-downtime key rotation |
| `REVOKED_API_KEYS` | Comma-separated denylist |
| `ALLOWED_ORIGINS` | CORS allowed origins |
| `RATE_LIMIT_REQUESTS` | Requests per window (default 60) |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window (default 60) |
| `REDIS_URL` | Optional Redis for shared rate limiting |
| `LOG_LEVEL` | Logging verbosity (default `INFO`) |
| `ALLOWED_HOSTS` | Host header allowlist |

Database-specific servers (BI MCP) also need:
- `DATABASE_URL` — SQLAlchemy connection string

API Integration Hub needs:
- `SLACK_TOKEN`, `GITHUB_TOKEN`, `STRIPE_SECRET_KEY`

---

## Security Model

- **API key auth**: All protected endpoints require `X-API-Key: <key>` header.
  Implemented in `showcase-servers/common/security.py`.
- **Rate limiting**: Configurable per `.env`. Redis-backed for multi-instance deployments.
- **CORS**: Explicit allowlist via `ALLOWED_ORIGINS`.
- **Audit logging**: Every tool call logged via `showcase-servers/common/audit.py`.
- **Tracing**: OpenTelemetry support via `showcase-servers/common/tracing.py`.
- **Bandit**: Security scanning config in `.bandit` at repo root.
- **Trivy**: CVE scanning; ignore rules in `.trivyignore`.
- **Key rotation**: Use overlap+revoke flow. See `showcase-servers/common/SECURITY-HARDENING.md`.

For `nosec` annotations: only use `B404` (subprocess import) and `B603` (subprocess.run with
list — safe when no shell=True). Never suppress `B602` (shell=True) or injection-class banners.

---

## MCP Tool Authoring Conventions

All MCP tools across all showcase servers must follow these rules:

```python
from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("server-name")

@mcp.tool()
async def my_tool(query: str = "") -> str:
    """One-line description only — multi-line breaks some MCP clients."""
    return f"Result: {query}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

- `@mcp.tool()` on async functions only.
- **Single-line docstrings** — multi-line breaks some MCP clients.
- Default parameters to `""` not `None`.
- Return formatted strings, not raw objects.
- Log to `sys.stderr`, not `stdout`.
- Run as non-root in Docker.
- Mount MCP at `/mcp` in FastAPI apps: `app.mount("/mcp", mcp.streamable_http_app())`.

---

## Scripts Reference

All scripts live in `scripts/`. PowerShell scripts target Windows; `.sh` scripts target Linux/macOS.

| Script | Platform | Purpose |
|--------|----------|---------|
| `sync-all.ps1` / `sync-all.sh` | Win/Lin | Rsync all three repos to t3610 |
| `status-all.ps1` / `status-all.sh` | Win/Lin | Local + remote health check |
| `start-claude-ready.ps1` | Win | Full ready sequence: harden → tunnel → health → launch Claude |
| `start-claude-mcp-tunnel.ps1` | Win | SSH tunnel to t3610 (ports 18009/18101–18104) |
| `check-claude-mcp-health.ps1` | Win | MCP endpoint health check |
| `harden-claude-mcp-config.ps1` | Win | Backup + no-BOM JSON write + schema validate Claude Desktop config |
| `monitor-mcp-stack.ps1` | Win | Probe all servers with severity exit codes |
| `install-mcp-monitor-task.ps1` | Win | Install/remove 1-min Windows Task Scheduler monitor |

### Common sync workflow

```powershell
# Sync to t3610 and restart Docker
./scripts/sync-all.ps1 -RemoteAlias t3610 -RemoteBase /home/jrm_fusional/Projects -RestartDocker

# Sync without restart
./scripts/sync-all.ps1 -RemoteAlias t3610 -RemoteBase /home/jrm_fusional/Projects
```

```bash
./scripts/sync-all.sh --remote t3610 --remote-base /home/jrm_fusional/Projects --restart-docker
```

### Claude Desktop launch sequence

```powershell
# Local servers
./scripts/start-claude-ready.ps1

# Remote via SSH tunnel
./scripts/start-claude-ready.ps1 -UseTunnel -RemoteAlias t3610

# CI / non-interactive
./scripts/start-claude-ready.ps1 -UseTunnel -SkipLaunchClaude -NonInteractive
```

---

## Claude Desktop Config

Config file locations:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
  (do NOT use `%APPDATA%` in the path — hardcode the full path)
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "business-intelligence": {
      "type": "streamable-http",
      "url": "http://just2awesome:8088/bi/"
    },
    "api-integration": {
      "type": "streamable-http",
      "url": "http://just2awesome:8088/api/"
    },
    "content-automation": {
      "type": "streamable-http",
      "url": "http://just2awesome:8088/content/"
    },
    "intelligence": {
      "type": "streamable-http",
      "url": "http://just2awesome:8088/intel/"
    }
  }
}
```

For local-only access via SSH tunnel, replace hostnames with `localhost` and ports with
tunnel ports (`18101`, `18102`, `18103`, `18104`).

**Windows JSON traps to avoid:**
- Write config with no BOM: `[System.IO.File]::WriteAllText(path, content, New-Object System.Text.UTF8Encoding($false))`
- Use forward slashes or escaped double backslashes in paths.
- Do not use `%APPDATA%` — Claude Desktop does not expand env vars.
- Cap registry at ≤8 servers on i5/i7 7th-gen hardware (timeout threshold).

---

## Docker Build Notes

- All server `Dockerfile`s build from `showcase-servers/` as context:
  `docker build -t <name> -f showcase-servers/<name>/Dockerfile ./showcase-servers/`
- The `docker-compose.yaml` handles this with `context: ./showcase-servers`.
- The Intelligence MCP uses a separate `Dockerfile.intelligence` at the repo root.
- Non-root execution is required in all Dockerfiles.

---

## Cross-Repo Dependencies

This repo is the **dependency provider** for the other repos:

| What | Consumer | Path |
|------|----------|------|
| `showcase-servers/common/security.py` | `fusional/core/main.py` | Runtime import via path search |
| `showcase-servers/common/audit.py` | `fusional/core/main.py` | Runtime import |
| `showcase-servers/common/tracing.py` | `fusional/core/main.py` | Runtime import |
| All MCP servers (ports 8101–8105) | `fusional` gateway | Pre-registered in `REGISTRY` |
| MCP server endpoints | `christopher-ai` | Via `FUSIONAL_*_URL` env vars |

Local development assumes all three repos are siblings in `~/Projects/`:
```
~/Projects/
├── mcp-consulting-kit/
├── FusionAL/              # or fusional/
└── Christopher-AI/        # or christopher-ai/
```

---

## Docs Index

| Doc | Purpose |
|-----|--------|
| `docs/TROUBLESHOOTING.md` | Symptom → cause → fix matrix |
| `docs/SYNC-AND-FRONTEND.md` | Full sync + frontend build guide |
| `docs/CLOUDFLARE-TUNNEL-SETUP.md` | Remote secure access via Cloudflare |
| `docs/GIT-AUTH-SETUP.md` | Git auth setup and recovery |
| `docs/T3610-MCP-OPS-HARDENING-RUNBOOK.md` | t3610 ops hardening |
| `docs/T3610-CHRISTOPHER-RUNBOOK.md` | Christopher deployment on t3610 |
| `docs/NEW-SERVER-INTAKE-NOTES.md` | Adding a new MCP server |
| `docs/NEW-SERVER-CUTOVER-CHECKLIST.md` | New server go-live checklist |
| `docs/SMITHERY-SUBMISSION-PACK.md` | Smithery marketplace submission |
| `CHANGELOG.md` | Version history |
| `ROADMAP.md` | Planned features |
| `CASE-STUDIES.md` | Client case studies |
| `INTEGRATION-CHANGES-AND-INSTRUCTIONS.md` | Integration migration notes |

---

## Adding a New MCP Server

1. Create `showcase-servers/<server-name>/` with: `Dockerfile`, `<server>.py`, `requirements.txt`, `.env.example`.
2. Add the service to `docker-compose.yaml` following the existing pattern.
3. Import `security.py` from `showcase-servers/common/` at startup.
4. Pick an unused port (next available after 8105).
5. Register the server in FusionAL's gateway catalog (see `fusional/core/main.py` `_SHOWCASE_SERVERS`).
6. Add the server to the Claude Desktop config and sync scripts.
7. Follow `docs/NEW-SERVER-INTAKE-NOTES.md` and `docs/NEW-SERVER-CUTOVER-CHECKLIST.md`.

---

## Key Conventions

- Python 3.11+ required across all servers.
- Pinned versions in `requirements.txt` — no loose `>=` without a security rationale.
- Security transitive deps: always pin `setuptools`, `jaraco.context`, `wheel` to patched versions (see `core/requirements.txt` in fusional for the current known-good set).
- No shell=True in subprocess calls. Use list form.
- All secrets in `.env`, never committed. `.gitignore` covers `.env`.
- JSON configs written with explicit no-BOM UTF-8 on Windows.
- `LOG_HEALTH_REQUESTS=false` in production to suppress `/health` log noise.
