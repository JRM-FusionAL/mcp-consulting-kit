# MCP Implementation Service Kit

Everything you need to run a done-for-you AI automation implementation service.

This repo contains:

- **Four platform servers** (FastAPI + Docker)
  - Business Intelligence MCP (databases) — port 8101
  - API Integration Hub (Slack, GitHub, Stripe) — port 8102
  - Content Automation MCP (scraping, monitoring) — port 8103
  - FusionAL Execution Engine (dynamic code + server generation) — port 8001
- **Consulting materials**
  - Landing page
  - Outreach strategy & templates
  - Pitch deck outline
  - Quick-start execution plan
- **Project scaffolding**
  - Roadmap
  - Changelog
  - Case studies

---

## Positioning

- This repository is a **service delivery framework**, not a packaged software product.
- You are selling implementation outcomes: workflow automation, system integration, and team onboarding.
- Revenue model: fixed-fee installs + monthly support/optimization retainers.

---

## Architecture

```text
Claude Desktop
    │
    │  (MCP)
    ▼
docker/mcp-gateway
    │
    ├── Business Intelligence MCP    (port 8101)
    │       └── Databases (PostgreSQL / MySQL / SQLite)
    ├── API Integration Hub          (port 8102)
    │       └── APIs (Slack / GitHub / Stripe / custom)
    ├── Content Automation MCP       (port 8103)
    │       └── Web / RSS / scraping targets
    └── FusionAL Execution Engine    (port 8001)  ◄── [dynamic engine]
            ├── /execute  → Docker-sandboxed Python
            ├── /register → runtime server registration
            └── /catalog  → unified server registry (all 4 servers)
```

FusionAL is the platform's runtime engine. The 3 showcase servers handle fixed integrations.
FusionAL handles anything that doesn't exist yet — execute code on the fly, AI-generate new
MCP servers, register them live without restarting anything.

---

## Launch all servers

### Windows (Batch)

Double-click `launch-all-servers.bat` in the repo root to start all MCP servers and FusionAL in separate windows.

### PowerShell

Run `launch-servers.ps1` from the repo root for the same effect.

### Docker Compose (Optional)

See `docker-compose.yaml` for containerized launch of all servers (requires Docker Desktop).

---

## .env Files

Each server requires a `.env` file (see `.env.example` in each directory). Fill in API keys and DB URLs as needed. **Never commit secrets.**

---

## Security smoke test

Run both shared security tests and BI security endpoint tests with one command:

```powershell
.\scripts\run-security-smoke.ps1
```

## Security hardening references

- Shared runbook: `showcase-servers/common/SECURITY-HARDENING.md`
- API key rotation/revocation uses `API_KEYS` and `REVOKED_API_KEYS`
- Shared rate-limiting can use Redis via `REDIS_URL` with in-memory degraded fallback
- CI vulnerability waivers are tracked in `.trivyignore` and SEC-TRACKER issue #11
- FusionAL uses the same `common/security.py` — all 4 servers share a single security model
