# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] - 2026-11-25 - Dependency Updates

### Security
- `soupsieve` 2.10 -> 4.1.3 (social-poster-mcp; CVE-2026-126190, CVE-2026-126191, CVE-2026-126193). beautifulsoup4 4.15.0 requires only `soupsieve>=1.6.1`; CSS selectors verified.
- `dnspython` 2.9.1 -> 2.9.2 (social-poster-mcp; CVE-2026-128089)
- `msgpack` floor >=1.2.1 -> >=1.2.3 (business-intelligence-mcp; CVE-2026-114613)

### Changed
- `fastapi` 0.162.0 -> 0.165.0 (all showcase servers)
- `pydantic` 2.14.2 -> 2.14.4 and `pydantic_core` 2.50.2 -> 2.50.5 (pydantic 2.14.4 requires pydantic-core==2.50.5)
- `sqlalchemy` 2.1.6 -> 2.1.9, `pymysql` 1.2.3 -> 1.2.4 (business-intelligence-mcp, social-poster-mcp)
- social-poster-mcp patch/minor bumps: annotated-doc, atproto, certifi, charset-normalizer, click, decorator, filelock, importlib_metadata, markdown-it-py, Mastodon.py, mypy_extensions, packaging, pydantic-settings, pytest-asyncio, python-multipart, PyYAML, ruff, sse-starlette, stevedore, typing-inspection
- `Dockerfile.intelligence`: mcp 1.26.0 -> 1.30.0, fastapi 0.138.1 -> 0.165.0, pandas 2.2.1 -> 2.3.3

### Changed (major versions)
- `redis` 7.4.1 -> 8.2.0 (api-integration-hub, business-intelligence-mcp, content-automation-mcp, social-poster-mcp). The rate limiter only uses `from_url`, `ping`, `incr` and `expire`, verified against a live Redis.
- `anthropic` 0.125.0 -> 2.14.0 and `openai` 2.54.0 -> 3.59.0 (business-intelligence-mcp, social-poster-mcp). Both now use `httpx2`. anthropic 2.x sends API version `2026-10-21`; `ClaudeProvider` sends no `temperature`/`top_p`/`top_k`, so nothing changes for it.
- social-poster-mcp: `wrapt` 1.17.3 -> 2.5.2, `python-dateutil` 2.9.0.post0 -> 4.0.0, `typer` 0.27.3 -> 0.29.2, `jiter` 0.18.0 -> 0.19.0, `librt` 0.16.0 -> 0.17.0. New pinned transitive deps: `httpx2`, `httpcore2`, `truststore`, `tzdata`.
- frontend: `react` / `react-dom` ^18.3.1 -> ^19.3.1 (already uses `createRoot`; matches `app/`)

### Held back
- `mcp` stays on 1.30.0. mcp 2.x removes `mcp.server.fastmcp` (renamed to `mcp.server.mcpserver.MCPServer`), and every server imports it.
- `libipld` stays on 3.5.0 because `atproto` 0.0.75 requires `libipld<4`.

---

## [0.4.1] - 2026-03-12 - Dependency Updates

### Changed
- `redis` 7.2.1 -> 7.3.0 (all showcase servers + FusionAL)
- `openai` 2.20.0 -> 2.26.0 (FusionAL core)
- `sqlalchemy` 2.0.47 -> 2.0.48 (business-intelligence-mcp)
- `fastmcp` >=0.4.0 -> >=3.1.0 (github-mcp-safe)
- `react` ^18.3.1 -> ^19.2.4 (frontend)
- `react-dom` ^18.3.1 -> ^19.2.4 (frontend)
- `vite` ^5.4.10 -> ^8.0.0 (frontend)
- `@vitejs/plugin-react` ^4.3.2 -> ^5.2.0 (frontend)

### Notes
- All other packages already at latest as of 2026-03-12
- React 19 compatible — app already uses createRoot, no deprecated APIs
- fastmcp v3.x is a major version bump — test github-mcp-safe after upgrading

---

## [0.4.0] - 2026-02-23 - FusionAL Integration

### Added
- FusionAL execution engine merged as 4th platform server (port 8009)
  - `/execute` — sandboxed Python execution with optional Docker isolation
  - `/register` — dynamic MCP server registration at runtime
  - `/catalog` — queryable registry of all servers (showcase + dynamic)
- FusionAL now uses shared `showcase-servers/common/security.py` (API key auth + rate limiting)
- Pre-seeded FusionAL registry with all 3 showcase servers on startup
- `launch-servers.ps1` updated to launch all 4 servers
- `test-servers.ps1` updated to health-check FusionAL
- `custom.yaml` MCP gateway catalog updated with FusionAL endpoints + all 3 showcase servers
- `.env.example` added to FusionAL root
- `fusional-agent` added to Copilot delegation model

### Architecture
- Platform is now **static + dynamic**: showcase servers handle fixed integrations, FusionAL handles runtime-generated and AI-authored MCP servers
- Claude Desktop can now request new tools mid-conversation via `fusional-execute` and `fusional-register` gateway tools

---

## [0.3.0] - 2026-02-23 - Security Hardening & Public Release Prep

### Added
- Shared security module (`showcase-servers/common/security.py`) with rate limiting, API key auth, and input validation
- Security hardening runbook (`showcase-servers/common/SECURITY-HARDENING.md`)
- Phase 2 hardening notes (`showcase-servers/common/P2-HARDENING.md`)
- Security smoke test scripts (`scripts/run-security-smoke.ps1`, `scripts/run-security-smoke.cmd`)
- GitHub Actions CI workflow (`.github/workflows/security-smoke.yml`)
- Trivy vulnerability waiver tracking (`.trivyignore`)
- `.env.example` files for all three showcase servers — safe for public repos
- `test-servers.ps1` — one-command local test runner for all servers
- `launch-servers.ps1` — one-command startup for all servers

### Changed
- Fixed all Linux `/home/` paths in `QUICK-START.md` -> correct Windows-relative paths
- Updated all bash code blocks -> PowerShell
- Fixed landing page filename reference (`landing-page.html` -> `index.html`)
- Replaced dead Discord `[link]` placeholders with real URLs
- Updated `.gitignore` to exclude `.env` and build artifacts

### Security
- Confirmed `.env` files are excluded from git history across all commits
- Real Anthropic API key identified and flagged for rotation before public release
- Docker isolation confirmed across all three servers

---

## [0.2.0] - 2026-02-19 - Consulting Materials Expansion

### Added
- `consulting-materials/business-model-overview.md` — service packages, pricing, GTM strategy
- `consulting-materials/market-launch-plan.md` — week-by-week launch execution plan
- `consulting-materials/OPERATOR-PLAYBOOK.md` — non-technical operator guide for running installs
- `consulting-materials/human-helper-job-description.md` — hiring guide for a virtual assistant
- `consulting-materials/assistant-agreement.md` — contractor agreement template
- `consulting-materials/WINDOWS-DEMO-GUIDE.md` — Windows-specific demo walkthrough
- `CASE-STUDIES.md` — three reference case studies (SaaS, agency, startup)
- `ROADMAP.md` — versioned feature roadmap through v1.0.0
- `launch-servers.ps1` — PowerShell script to launch all servers simultaneously

### Changed
- Expanded `pitch-deck-outline.md` to 17 slides with presenter notes and customization tips
- Updated `outreach-strategy.md` with objection handling, value-based pricing formula, and retainer math

---

## [0.1.0] - 2026-02-17 - Initial Reconstruction

### Added
- Three FastAPI-based MCP showcase servers:
  - `showcase-servers/business-intelligence-mcp/` — natural language database queries (PostgreSQL, MySQL, SQLite)
  - `showcase-servers/api-integration-hub/` — Slack, GitHub, Stripe integrations
  - `showcase-servers/content-automation-mcp/` — web scraping, RSS, change monitoring
- Dockerfiles and `requirements.txt` for each server
- Individual `README.md` per server with setup and usage examples
- `consulting-materials/index.html` — full landing page with hero, pricing, case studies, contact form
- `consulting-materials/outreach-strategy.md` — cold email templates, LinkedIn scripts, discovery call script
- `consulting-materials/pitch-deck-outline.md` — 17-slide pitch deck outline
- `consulting-materials/QUICK-START.md` — 30-day launch playbook
- `consulting-materials/COMPLETE-INVENTORY.md` — full kit index
- Root `README.md` with architecture diagram and repo overview
- `.gitignore` configured to exclude `.env`, `__pycache__`, build artifacts

---

## [0.0.1] - Internal Only

- Initial consulting kit concept and business materials drafted
