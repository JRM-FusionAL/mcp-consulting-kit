# MCP Implementation Service Kit

Everything you need to run a done-for-you AI automation implementation service.

This repo contains:

- **Three implementation blueprints** (FastAPI + Docker)
  - Business Intelligence MCP (databases)
  - API Integration Hub (Slack, GitHub, Stripe)
  - Content Automation MCP (scraping, monitoring)
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
FastAPI MCP servers (Docker)
    │
    ├── Databases (PostgreSQL / MySQL / SQLite)
    ├── APIs (Slack / GitHub / Stripe / custom)
    └── Web / RSS / scraping targets
```

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
