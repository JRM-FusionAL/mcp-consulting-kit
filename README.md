# MCP Consulting Kit

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-orange)
![Stars](https://img.shields.io/github/stars/JonathanMelton-FusionAL/mcp-consulting-kit?style=social)

Three production-grade MCP servers + FusionAL execution engine. Done-for-you AI automation implementation service framework.

**Works on Windows, Linux, and macOS.**

---

## What's in here

| Server | Port | What it does |
|---|---|---|
| Business Intelligence MCP | 8101 | Natural language → SQL (PostgreSQL / MySQL / SQLite) |
| API Integration Hub | 8102 | Slack, GitHub, Stripe via natural language |
| Content Automation MCP | 8103 | Web scraping, RSS feeds, link extraction |
| Intelligence MCP | 8104 | Hot-topic discovery, business lead sourcing, trending repo intelligence |
| FusionAL Execution Engine | 8009 | Dynamic code execution + MCP server registry |

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/JonathanMelton-FusionAL/mcp-consulting-kit
cd mcp-consulting-kit
```

### 2. Install dependencies

```bash
pip3 install fastapi uvicorn[standard] python-dotenv pydantic requests \
             beautifulsoup4 feedparser lxml sqlalchemy "mcp[cli]"
```

### 3. Configure

Copy `.env.example` to `.env` in each server directory and fill in your values:

```bash
cp showcase-servers/business-intelligence-mcp/.env.example showcase-servers/business-intelligence-mcp/.env
cp showcase-servers/api-integration-hub/.env.example showcase-servers/api-integration-hub/.env
cp showcase-servers/content-automation-mcp/.env.example showcase-servers/content-automation-mcp/.env
```

### 4. Launch

**Linux / macOS:**
```bash
chmod +x launch.sh
./launch.sh
```

**Windows:**
```cmd
launch-all-servers.bat
```

**Any platform (Python):**
```bash
python3 launch.py
```

### 5. Verify

```bash
curl http://localhost:8101/health
curl http://localhost:8102/health
curl http://localhost:8103/health
curl http://localhost:8104/health
curl http://localhost:8009/health
```

All should return success responses (`200 OK`).

If you are running behind the Nginx proxy, verify with:

```bash
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/healthz
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/bi/
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/api/
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/content/
curl -u 'mcpadmin:CHANGE_ME_STRONG_PASSWORD' http://just2awesome:8088/intel/
```

---

## Sync Across Local + Remote (t3610)

Syncs all three repos (`mcp-consulting-kit`, `FusionAL`, `Christopher-AI`) from your local `Projects` folder to remote `t3610`.

**Windows (PowerShell):**
```powershell
./scripts/sync-all.ps1 -RemoteAlias t3610 -RemoteBase /home/jrm_fusional/Projects
```

**Linux / macOS:**
```bash
chmod +x ./scripts/sync-all.sh
./scripts/sync-all.sh --remote t3610 --remote-base /home/jrm_fusional/Projects
```

To sync and restart remote Docker services:

```bash
# PowerShell
./scripts/sync-all.ps1 -RestartDocker

# Bash
./scripts/sync-all.sh --restart-docker
```

Full guide: `docs/SYNC-AND-FRONTEND.md`

Remote secure access guide (Cloudflare Tunnel): `docs/CLOUDFLARE-TUNNEL-SETUP.md`

Quick one-command status check (local + remote):

```powershell
./scripts/status-all.ps1 -RemoteAlias t3610
```

```bash
./scripts/status-all.sh --remote t3610
```

---

## Production Frontend

The production frontend lives in `frontend/` (Vite + React).

```bash
cd frontend
npm install
npm run build
```

Build output is generated in `frontend/dist`.

To run in Docker:

```bash
docker build -t mcp-kit-frontend ./frontend
docker run -p 3000:80 --rm mcp-kit-frontend
```

---

## Architecture

```
Claude Desktop / Christopher / Any MCP client
        │
        │  MCP protocol (Streamable HTTP)
        ▼
  ┌─────────────────────────────────────┐
  │  Business Intelligence MCP  :8101   │  Natural language → SQL
  │  API Integration Hub        :8102   │  Slack / GitHub / Stripe
  │  Content Automation MCP     :8103   │  Scraping / RSS
  │  Intelligence MCP           :8104   │  Trends / leads
  │  FusionAL Execution Engine  :8009   │  Dynamic code + registry
  └─────────────────────────────────────┘
```

Each server exposes:
- REST API endpoints
- MCP Streamable HTTP at `/mcp` (connect any MCP client)
- `/health` for monitoring

---

## Connecting to Claude Desktop

Add to `claude_desktop_config.json`:

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

For local-only access over SSH tunnel, replace `just2awesome` with `localhost`.

**Config file locations:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

---

## API Key Rotation

```bash
# Rotate all keys across all .env files at once
python3 rotate_keys.py

# Dry run first
python3 rotate_keys.py --dry-run

# Rotate and restart servers
python3 rotate_keys.py --restart
```

---

## Security

- API key auth on all endpoints (`X-API-Key` header)
- Rate limiting (configurable via `.env`)
- Shared security module: `showcase-servers/common/security.py`
- See `showcase-servers/common/SECURITY-HARDENING.md`

---

## Consulting Service

This repo is the technical foundation for a done-for-you MCP implementation service.

Current focus:
- Self-hosted MCP governance deployments
- Audit logging + policy enforcement rollout
- Privacy-first architecture for healthcare, legal, and fintech SMBs
- Engagement model: $150-$250/hour or fixed-scope pilot

- 📧 jonathanmelton004@gmail.com
- 📅 calendly.com/jonathanmelton004/30min
- 🔗 github.com/JonathanMelton-FusionAL/mcp-consulting-kit

## GTM Templates

- Smithery submission pack: `docs/SMITHERY-SUBMISSION-PACK.md`
- awesome-mcp-servers PR draft: `docs/AWESOME-MCP-SERVERS-PR-DRAFT.md`
- Distribution checklist: `docs/DISTRIBUTION-THIS-WEEK.md`

## Ops Runbooks

- Git auth setup/recovery: `docs/GIT-AUTH-SETUP.md`
- New server intake notes: `docs/NEW-SERVER-INTAKE-NOTES.md`
- New server cutover checklist: `docs/NEW-SERVER-CUTOVER-CHECKLIST.md`
- t3610 Christopher runbook: `docs/T3610-CHRISTOPHER-RUNBOOK.md`
