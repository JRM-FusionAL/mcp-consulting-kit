# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.4.0] – 2026-02-23 – FusionAL Integration

### Added
- FusionAL execution engine merged as 4th platform server (port 8001)
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

## [0.3.0] – 2026-02-23 – Security Hardening & Public Release Prep

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
- Fixed all Linux `/home/` paths in `QUICK-START.md` → correct Windows-relative paths
- Updated all bash code blocks → PowerShell
- Fixed landing page filename reference (`landing-page.html` → `index.html`)
- Replaced dead Discord `[link]` placeholders with real URLs
- Updated `.gitignore` to exclude `.env` and build artifacts

### Security
- Confirmed `.env` files are excluded from git history across all commits
- Real Anthropic API key identified and flagged for rotation before public release
- Docker isolation confirmed across all three servers

---

## [0.2.0] – 2026-02-19 – Consulting Materials Expansion

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

## [0.1.0] – 2026-02-17 – Initial Reconstruction

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

## [0.0.1] – Internal Only

- Initial consulting kit concept and business materials drafted
