# Copilot Instructions for MCP Consulting Kit

## Agent Delegation Model
- **agent-dople**: Responsible for maintaining server integrity, security, and stability, and for running each server (`business-intelligence-mcp`, `api-integration-hub`, `content-automation-mcp`, and the `FusionAL` execution engine on port 8001). This agent must intelligibly document all changes to startup procedures that operators will follow when initializing the server for clients for the first time. Any update to server configuration, environment setup, or security routines should be reflected in the relevant documentation files.

- **hunter-agent**: Responsible for keeping the quickstart guide up to date. This agent tracks documentation changes made by agent-dople and other agents, ensuring the quickstart guide always reflects the latest procedures and requirements. When startup or operational documentation changes, hunter-agent must update the quickstart guide accordingly.

- **master-agent**: Responsible for managing all commits and pushes to the repository. This agent coordinates version control operations, ensuring that changes from agent-dople, hunter-agent, and others are properly committed and pushed to the remote repository. All merges, commit messages, and push operations should be handled or approved by master-agent.

- **fusional-agent**: Responsible for the FusionAL execution engine (`C:\Users\puddi\projects\FusionAL\core\`). Manages dynamic MCP server registration, sandboxed code execution, and AI-generated server deployment. FusionAL is the platform's runtime engine — agent-dople manages the static showcase servers, fusional-agent manages everything dynamic. Security applied to FusionAL must follow the same conventions in `showcase-servers/common/security.py`.

## Big picture architecture
- This repo is a **service-delivery framework** with three static showcase servers under `showcase-servers/` plus the FusionAL dynamic execution engine:
  - `business-intelligence-mcp` (NL→SQL + DB execution) — port 8101
  - `api-integration-hub` (Slack/GitHub/Stripe wrappers) — port 8102
  - `content-automation-mcp` (scraping + RSS parsing) — port 8103
  - `FusionAL` (dynamic code execution, server generation, registry) — port 8001 at `C:\Users\puddi\projects\FusionAL\core\`
- Each showcase server is intentionally standalone (`main.py`, `mcp_tools.py`, `requirements.txt`, `Dockerfile`) and shares security/observability via `showcase-servers/common/security.py`.
- FusionAL uses the same `security.py` module, resolved via path discovery at startup.
- Request flow pattern: endpoint in `main.py` → Pydantic request model in `mcp_tools.py` → integration layer (`db.py`, `clients/*`, or `scraper.py`).
- FusionAL flow: Claude Desktop → `docker/mcp-gateway` → FusionAL `/execute`, `/register`, `/catalog` → Docker sandbox or dynamic server.
- All 4 servers launch together via `launch-servers.ps1` in the repo root.

## Security and middleware conventions (critical)
- Protected POST routes always compose both dependencies in this order:
  - `Depends(verify_api_key)`
  - `Depends(enforce_rate_limit)`
- Keep shared middleware bootstrap in every server startup:
  - `configure_cors(app)`
  - `configure_observability(app)`
  - `initialize_rate_limit_store(app)`
- API key model is rotation-friendly: `API_KEYS` (active), `API_KEY` (legacy fallback), `REVOKED_API_KEYS` (denylist).
- All responses should preserve `X-Request-ID`; security headers and log redaction are applied centrally in `common/security.py`.

## Service-specific behavior to preserve
- BI server (`showcase-servers/business-intelligence-mcp/`):
  - `handle_nl_query()` must run `normalize_sql()` + `validate_sql_is_safe()` before `run_query()`.
  - SQL safety is strict: read-only `SELECT`/`WITH`, single statement, no comments, and blocked write/DDL keywords.
  - LLM provider selection is env-driven (`LLM_PROVIDER=claude|rule|local`) in `llm_provider.py`; `local` is currently a placeholder.
- API hub (`showcase-servers/api-integration-hub/`): orchestration lives in `mcp_tools.py` (e.g., create GitHub issue then optional Slack notify).
- Content automation (`showcase-servers/content-automation-mcp/`): keep extraction logic in `scraper.py`; endpoints remain thin wrappers in `main.py`.

## Developer workflow (Windows-first)
- Security smoke tests (root):
  - `./scripts/run-security-smoke.ps1`
  - `scripts\run-security-smoke.cmd`
- The smoke script auto-discovers Python (`$env:VIRTUAL_ENV`, repo `.venv`, then system `python`) and runs:
  - `showcase-servers/common/test_security_common.py`
  - `showcase-servers/business-intelligence-mcp/test_security.py`
- Local server run pattern (inside each service folder):
  - `pip install -r requirements.txt`
  - `uvicorn main:app --host 0.0.0.0 --port <8101|8102|8103>`

## CI and repo quirks
- CI workflow is `.github/workflows/security-smoke.yml`.
- Vulnerability waivers belong in `.trivyignore` and should remain temporary.
- BI code, tests, and CI paths are standardized to `showcase-servers/business-intelligence-mcp/`.

## Change guidance for agents
- Prefer edits in shared security code (`showcase-servers/common/security.py`) over duplicating logic in individual services.
- Keep endpoint handlers thin: validation + orchestration in `mcp_tools.py`/clients, not in route functions.
- Preserve env-var compatibility (`API_KEY` fallback, port defaults, `REDIS_URL` degraded fallback behavior) unless asked to break compatibility.