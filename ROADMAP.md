
# Roadmap

## v0.1.0 – Initial Reconstruction ✅

- [x] Rebuild three MCP servers with FastAPI
- [x] Dockerize each server
- [x] Restore consulting materials
- [x] Add unified repo README
- [x] Add Quick Start, Roadmap, Changelog, Case Studies

## v0.4.0 – FusionAL Integration ✅

- [x] FusionAL execution engine merged as 4th platform server (port 8009)
- [x] Dynamic MCP server registration via `/register`
- [x] Sandboxed Python code execution via `/execute`
- [x] Unified server catalog via `/catalog` (all 4 servers)
- [x] FusionAL secured via shared `common/security.py`
- [x] All 4 servers in unified `launch-servers.ps1`
- [x] MCP gateway `custom.yaml` updated to expose all endpoints

## v0.3.0 – Production Hardening ✅

- [x] Add auth for API endpoints (shared `security.py` module with API key auth)
- [x] Add logging & metrics (security smoke test scripts and GitHub Actions CI)
- [x] Add tests for each server (`test-servers.ps1`, security hardening runbook)
- [x] Add CI workflow (`.github/workflows/security-smoke.yml`)
- [x] Track detailed security hardening backlog in GitHub Issues (SEC-01 to SEC-10)

## v0.2.0 – Unified Server & Local AI ✅

- [x] Abstract LLM provider behind interface (`llm_provider.py` in BI server)
- [x] Add `LLM_PROVIDER` env switch (`claude` / `rule` / `local`)
- [x] Implement local provider stub

## v1.0.0 – Production Release (Target: April 2026)

- [ ] Policy profiles (`strict` / `balanced` / `dev`)
- [ ] Tenant-scoped API keys with revocation workflow
- [ ] Tool call audit export (JSON/CSV)
- [ ] MCP Security Audit report template
- [ ] One-command health check across all servers
- [ ] Updated docs with governance walkthrough
- [ ] Polish docs and tag v1.0.0

## v1.1.0 – Enterprise Features (Target: June 2026)

- [ ] RBAC integration (map to existing IdP)
- [ ] Rate-limit policy presets per tenant
- [ ] Error budget tracking and alerting
- [ ] Compliance report generator (HIPAA/SOC 2 checklist output)
- [ ] Multi-client configuration templates

## v2.0.0 – Platform (Target: Q4 2026)

- [ ] Web dashboard for governance operations
- [ ] Christopher-AI voice integration
- [ ] Channel partner white-label mode
- [ ] Automated MCP server health monitoring
- [ ] Managed ops control panel for retainer clients
