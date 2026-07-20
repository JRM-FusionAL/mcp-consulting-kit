# MCP Consulting Kit — Architecture Guide

**Version:** 1.0.0  
**Updated:** 2026-07-15  
**Project:** [mcp-consulting-kit](https://github.com/JonathanMelton-FusionAL/FusionAL-mcp-consulting-kit)

---

## Table of Contents

1. [Purpose](#purpose)
2. [High-Level Architecture](#high-level-architecture)
3. [Server Overview](#server-overview)
4. [Client Engagement Flow](#client-engagement-flow)
5. [Showcase Servers Detail](#showcase-servers-detail)
6. [Intelligence MCP Detail](#intelligence-mcp-detail)
7. [FusionAL Execution Engine](#fusional-execution-engine)
8. [Shared Modules](#shared-modules)
9. [Deployment Patterns](#deployment-patterns)
10. [Frontend & UI](#frontend--ui)
11. [CI/CD & Maintenance](#cicd--maintenance)
12. [Consulting Materials](#consulting-materials)
13. [Security Model](#security-model)
14. [Directory Structure](#directory-structure)

---

## Purpose

The MCP Consulting Kit is a **production-grade, turnkey stack** of MCP (Model Context Protocol) servers paired with a **done-for-you consulting service framework**. It enables teams to deploy governed AI automation — connecting databases, APIs, and web content to conversational AI interfaces (Claude Desktop, any MCP client) — in under 15 minutes.

The project serves two audiences simultaneously:

| Audience | What they get |
|---|---|
| **Technical users / clients** | Self-hosted MCP servers with REST + MCP Streamable HTTP, shared security, and Docker deployment |
| **Consultants / operators** | Full go-to-market bundle: landing page, outreach templates, pricing models, operator playbook, and runbooks |

---

## High-Level Architecture

```
                     ┌─────────────────────────────────────┐
                     │     Any MCP Client (Claude Desktop,   │
                     │     Cursor, custom MCP host, etc.)    │
                     └────────────────┬────────────────────┘
                                      │
                                      │  MCP Streamable HTTP
                                      │  (HTTP POST/SSE to /mcp)
                                      ▼
     ┌────────────────────────────────────────────────────────────────┐
     │                                                               │
     │                     Nginx Reverse Proxy                        │
     │                 (port 8088, Basic Auth)                        │
     │                                                               │
     │  /bi/      → business-intelligence-mcp:8101                   │
     │  /api/     → api-integration-hub:8102                         │
     │  /content/ → content-automation-mcp:8103                      │
     │  /intel/   → intelligence-mcp:8104                            │
     │  /fusional/ → fusional-execution-engine:8009                  │
     └────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
                    ▼                 ▼                  ▼
     ┌─────────────────────┐ ┌──────────────┐ ┌──────────────────┐
     │ Business            │ │ API          │ │ Content          │
     │ Intelligence MCP    │ │ Integration  │ │ Automation MCP   │
     │ :8101               │ │ Hub :8102    │ │ :8103            │
     ├─────────────────────┤ ├──────────────┤ ├──────────────────┤
     │ Natural Language    │ │ Slack        │ │ Web scraping     │
     │ → SQL (PostgreSQL,  │ │ GitHub       │ │ RSS feed parsing │
     │   MySQL, SQLite)    │ │ Stripe       │ │ Link extraction  │
     └─────────────────────┘ └──────────────┘ └──────────────────┘

     ┌──────────────────────────┐  ┌──────────────────────────┐
     │ Intelligence MCP :8104   │  │ GitHub MCP Safe :8105    │
     ├──────────────────────────┤  ├──────────────────────────┤
     │ Hot topic aggregation    │  │ Rate-limited GitHub MCP  │
     │ Business lead discovery  │  │ tool access              │
     │ Trend intelligence       │  │                          │
     └──────────────────────────┘  └──────────────────────────┘

     ┌─────────────────────────────────────────────────────┐
     │  FusionAL Execution Engine :8009                     │
     │  Dynamic code execution + MCP server registry       │
     └─────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
              PostgreSQL        External APIs        Web Content
              SQLite            Slack / GitHub        HTML pages
              MySQL             Stripe                RSS feeds
```

### Communication Patterns

| Layer | Protocol | Details |
|---|---|---|
| **MCP Client → Proxy** | HTTP/HTTPS | Streamable HTTP transport (POST for requests, SSE for streaming responses) |
| **MCP Client → Direct** | HTTP | Direct to server ports (8101-8105, 8009) for local dev |
| **Proxy → Servers** | HTTP | Nginx reverse-proxies path-based routes to internal container names |
| **Servers ↔ External** | HTTPS | Outbound calls to APIs (GitHub, Slack, Stripe, HN, Reddit, etc.) |
| **Servers ↔ DB** | PostgreSQL/MySQL/SQLite | Business Intelligence MCP only |

Each server exposes three endpoint categories:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check — returns `{"status": "ok"}` |
| `POST /mcp` (or `/`) | MCP Streamable HTTP — tool invocation, session management |
| `POST /<action>` | REST-specific endpoints (e.g. `/nl-query`, `/slack/send`, `/scrape/article`) |

---

## Server Overview

| Server | Port | Purpose | Key Tools / Endpoints |
|---|---|---|---|
| **Business Intelligence MCP** | 8101 | Natural language → SQL queries against databases | `nl-query`, MCP `query_database`, schema exploration |
| **API Integration Hub** | 8102 | Slack messaging, GitHub issues, Stripe customer lookup | `slack_send`, `github_create_issue`, `stripe_customer_lookup` |
| **Content Automation MCP** | 8103 | Web scraping, RSS feed parsing, table/link extraction | `scrape_article`, `scrape_links`, `scrape_tables`, `parse_rss` |
| **Intelligence MCP** | 8104 | Hot topic aggregation, business lead discovery, trending repos | `intelligence_get_hot_topics`, `intelligence_find_business_leads`, `intelligence_get_trending_repos`, `intelligence_daily_pulse` |
| **GitHub MCP Safe** | 8105 | Rate-limited GitHub MCP tool access | MCP tools wrapping GitHub API |
| **FusionAL Execution Engine** | 8009 | Dynamic sandboxed Python execution, MCP server registry | `/execute`, `/register`, `/catalog` |

---

## Client Engagement Flow

```
                     ┌──────────────────────┐
                     │  1. Discovery Call    │
                     │  (Pain points, tech   │
                     │   stack, success      │
                     │   criteria, budget)   │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  2. Implementation   │
                     │     Plan (1-page)    │
                     │  Workflows, systems, │
                     │  timeline, pricing   │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  3. Pre-Install Prep  │
                     │  Credential collection│
                     │  API key harvesting   │
                     │  Environment check    │
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                  ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
     │ Session 1:   │ │ Session 2:   │ │ Session 3:       │
     │ Initial Setup│ │ Claude       │ │ Workflow Testing │
     │ Docker/.env  │ │ Desktop      │ │ All 3 workflows  │
     │ + health     │ │ Integration  │ │ + fixes          │
     └──────────────┘ └──────────────┘ └──────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  4. Rollout &        │
                     │     Training         │
                     │  45-min team session │
                     │  Handoff docs        │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  5. Monthly Support   │
                     │  Bug fixes, updates,  │
                     │  1-2 workflows/mo     │
                     │  Quarterly review     │
                     └──────────────────────┘
```

### Feature Intake Loop

The **ENGAGEMENT-FEATURE-INTAKE-LOOP** documents how every consulting call generates upstream product features:

1. Ask 5 discovery questions on every call (compliance blockers, audit needs, access segmentation, etc.)
2. Capture feature signals per account (pain, urgency, revenue impact, exact buyer language)
3. Score using `pain_frequency (0-4) + deal_impact (0-4) + implementation_speed (0-2)`
4. Ship highest-score feature into FusionAL enterprise tier
5. Weekly cadence: review → lock → implement → ship changelog

---

## Showcase Servers Detail

### Business Intelligence MCP

**Files:** `showcase-servers/business-intelligence-mcp/`

| Source File | Role |
|---|---|
| `main.py` | FastAPI app, mounts MCP transport, REST endpoints |
| `mcp_tools.py` | MCP tool definitions (query, schema, tables) |
| `db.py` | Database connection abstraction (PostgreSQL/MySQL/SQLite) |
| `llm_provider.py` | LLM abstraction layer (Claude / rule-based / local provider) |
| `mcp_transport.py` | MCP Streamable HTTP transport configuration |
| `security.py` | Per-server security (API key check, rate limiting) |

**Architecture notes:**
- Abstracted LLM provider via `LLM_PROVIDER` env switch: `claude`, `rule`, `local`
- Database type auto-detected from `DB_URL` connection string
- Schema introspection before query generation

### API Integration Hub

**Files:** `showcase-servers/api-integration-hub/`

| Source File | Role |
|---|---|
| `main.py` | FastAPI app with REST endpoints + MCP mount |
| `mcp_tools.py` | Slack / GitHub / Stripe tool functions |
| `clients/slack_client.py` | Slack Web API wrapper |
| `clients/github_client.py` | GitHub REST API wrapper |
| `clients/stripe_client.py` | Stripe API wrapper |
| `clients/rate_limiter.py` | Per-client rate limiting |

**Architecture notes:**
- Each external API wrapped in a dedicated client module
- REST endpoints mirror MCP tool functionality for non-MCP clients
- `.well-known/mcp/server-card.json` for MCP server discovery

### Content Automation MCP

**Files:** `showcase-servers/content-automation-mcp/`

| Source File | Role |
|---|---|
| `main.py` | FastAPI app with scraping REST endpoints + MCP mount |
| `mcp_tools.py` | MCP tools: scrape, RSS, link extraction |
| `scraper.py` | BeautifulSoup-based HTML parsing engine |
| `security.py` | Per-server security |

**Architecture notes:**
- Stateless — no persistent storage
- RSS feed parsing via `feedparser`
- Table extraction with CSV and JSON output formats

### GitHub MCP Safe

**Files:** `showcase-servers/github-mcp-safe/`

| Source File | Role |
|---|---|
| `main.py` | FastAPI + MCP lifespan-managed server |
| `mcp_tools.py` | GitHub MCP tool definitions |
| `mcp_transport.py` | MCP transport with security settings |

**Architecture notes:**
- Production-grade rate-limited GitHub MCP server
- Uses `asynccontextmanager` lifespan pattern (modern FastAPI)
- Graceful fallback when common security module is unavailable

---

## Intelligence MCP Detail

**File:** `intelligence_mcp.py` (runs standalone, port 8104)

A market intelligence server that aggregates hot topics and discovers business leads **with zero API keys required** — all sources are publicly scrapable.

### Internal Architecture

```
                     intelligence_mcp.py
                     ┌────────────────────────────┐
                     │     FastMCP Server          │
                     │  (via mcp.server.fastmcp)   │
                     └──────────┬─────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Hot Topics       │  │ Business Leads   │  │ Trending Repos   │
│ (MCP Tool 1)     │  │ (MCP Tool 2)     │  │ (MCP Tool 3)     │
│                  │  │                  │  │                  │
│ Concurrent fetch │  │ Curated database │  │ GitHub Trending  │
│ from 5 sources   │  │ filtered by      │  │ scrape + lang/   │
│ ranked by score  │  │ niche + intent   │  │ period filter    │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

| Source | Fetch Method | Data |
|---|---|---|
| Hacker News | Firebase API (`/v0/topstories.json`) | Top stories by score |
| Reddit | JSON API (`/r/{sub}/hot.json`) | 7 AI/dev/MCP subreddits |
| Dev.to | REST API (`/api/articles`) | Top articles, last 7 days |
| GitHub Trending | HTML scrape (`github.com/trending`) | Repos with stars, language |
| Product Hunt | HTML scrape + Next.js data | Daily top products |

**Tool 4 — Daily Pulse:** Aggregates Tools 1–3 into a single `intelligence_daily_pulse()` call for morning briefing.

---

## FusionAL Execution Engine

**Port:** 8009 (from the separate `FusionAL/core` repository)

The FusionAL Execution Engine provides two core capabilities:

| Feature | Endpoint | Description |
|---|---|---|
| **Dynamic Server Registry** | `POST /register` | Register external MCP servers at runtime |
| **Sandboxed Code Execution** | `POST /execute` | Run Python code in a sandboxed environment |
| **Server Catalog** | `GET /catalog` | List all registered MCP servers in the mesh |

The engine integrates with the consulting kit's shared security module (`common/security.py`) and is included in the unified launch and proxy setup.

---

## Shared Modules

All showcase servers (and FusionAL) consume a common security library:

### `showcase-servers/common/security.py`

| Function | Purpose |
|---|---|
| `configure_cors(app)` | CORS middleware with validated allowlist (no wildcards) |
| `configure_observability(app)` | Request logging middleware with request ID, redacted headers, timing |
| `initialize_rate_limit_store(app)` | In-memory + optional Redis rate limit store |
| `verify_api_key(request, x_api_key)` | API key authentication against `API_KEYS` env var |
| `enforce_rate_limit(request)` | Sliding-window rate limiter (configurable via `RATE_LIMIT_*`) |
| `revoke_api_key(app, api_key)` | Runtime API key revocation |

### `showcase-servers/common/security_baseline.py`

| Feature | Detail |
|---|---|
| `TrustedHostMiddleware` | Rejects requests from unknown hosts |
| `CORSMiddleware` | Restrictive CORS with explicit allowed origins |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `CSP`, `HSTS`, `Cache-Control` |
| Response timing | `X-Response-Time-ms` header |

### `showcase-servers/common/tracing.py`

- OpenTelemetry-based distributed tracing (optional dependency)
- Supports OTLP HTTP exporter (Jaeger/Tempo/Zipkin) or console exporter
- Auto-instruments FastAPI via `FastAPIInstrumentor`
- Graceful no-op fallback when `opentelemetry` packages are not installed

---

## Deployment Patterns

### Pattern 1: Local Development (Direct)

```
git clone <repo>
pip install -r requirements
python3 launch.py          # starts all servers on localhost ports
```

**Ports:** 8101-8105, 8009 — all bound to `127.0.0.1`.

### Pattern 2: Docker Compose (Local)

```
docker compose -f docker-compose.yaml up --build
```

| Container | Image Source | Internal Port |
|---|---|---|
| `api-integration-hub` | `./showcase-servers/api-integration-hub/Dockerfile` | 8102 |
| `business-intelligence-mcp` | `./showcase-servers/business-intelligence-mcp/Dockerfile` | 8101 |
| `content-automation-mcp` | `./showcase-servers/content-automation-mcp/Dockerfile` | 8103 |
| `intelligence-mcp` | `Dockerfile.intelligence` | 8104 |
| `github-mcp-safe` | `./showcase-servers/github-mcp-safe/Dockerfile` | 8105 |

All ports bound to `127.0.0.1` (not publicly accessible).

### Pattern 3: Nginx Reverse Proxy (Port 8088)

```
docker compose -f docker-compose.yaml -f docker-compose.proxy.yaml up --build
```

Adds an Nginx container (`mcp-proxy`) on port 8088 with:

- **Basic Auth** (via `.htpasswd`)
- **Path-based routing** to individual servers
- Single port for all MCP client configuration

| Route | Backend |
|---|---|
| `/bi/` | Business Intelligence MCP :8101 |
| `/api/` | API Integration Hub :8102 |
| `/content/` | Content Automation MCP :8103 |
| `/intel/` | Intelligence MCP :8104 |
| `/fusional/` | FusionAL :8009 |

### Pattern 4: Cloudflare Tunnel (Public Internet)

```
docker compose -f docker-compose.yaml -f docker-compose.proxy.yaml \
              -f docker-compose.cloudflare.yaml up --build
```

Adds a `cloudflared` sidecar that tunnels through Cloudflare, exposing the Nginx proxy via a public domain (`api.fusional.dev`, etc.). No open firewall ports required.

### Pattern 5: SSH Tunnel (Windows Clients)

For Windows clients behind restrictive networks, SSH tunnels forward remote server ports to localhost:

| Local Port | Remote Server |
|---|---|
| 18009 | FusionAL :8009 |
| 18101 | Business Intelligence MCP :8101 |
| 18102 | API Integration Hub :8102 |
| 18103 | Content Automation MCP :8103 |
| 18104 | Intelligence MCP :8104 |

Managed by `scripts/start-claude-mcp-tunnel.ps1` and `scripts/start-claude-ready.ps1`.

---

## Frontend & UI

### Production Frontend (`frontend/`)

| Aspect | Detail |
|---|---|
| Stack | React 18 + Vite 8 |
| Dockerfile | `frontend/Dockerfile` (Nginx-based static serving) |
| Port | 3000 (containerized) |
| Build | `npm run build` → `frontend/dist/` |

### Consulting Landing Page (`consulting-materials/index.html`)

Standalone HTML landing page with:

- Hero section with CTA
- Three service offering cards
- Pricing tiers ($3,500 Starter / $9,000 Growth / $3k/mo Managed)
- Case study examples
- Contact form

---

## CI/CD & Maintenance

### GitHub Actions

| Workflow | File | Purpose |
|---|---|---|
| Security Smoke | `.github/workflows/security-smoke.yml` | Runs CodeQL, `pip-audit`, smoke tests on PRs |
| Dependabot | `.github/dependabot.yml` | Automated dependency PRs |

### Automated Maintenance (Hermes Cron)

The project uses a Hermes cron job (`~/.hermes/cron/`) running `maintenance.sh` that:

1. Checks for outdated dependencies (Python pip, Node.js npm)
2. Opens PRs for safe minor/patch version bumps
3. Merges maintenance summary docs
4. Labels untriaged issues

See `MAINTENANCE.md` for full history.

---

## Security Model

| Layer | Mechanism | Env Config |
|---|---|---|
| **API Authentication** | `X-API-Key` header verified against `API_KEYS` | `API_KEYS`, `API_KEY` |
| **Key Revocation** | Runtime in-memory set + `REVOKED_API_KEYS` env | `REVOKED_API_KEYS` |
| **Rate Limiting** | Sliding-window in-memory (fallback from Redis) | `RATE_LIMIT_REQUESTS` (default: 60/min), `RATE_LIMIT_WINDOW_SECONDS` |
| **Redis** | Optional for distributed rate limiting | `REDIS_URL` |
| **CORS** | Explicit origin allowlist (no wildcards) | `ALLOWED_ORIGINS` |
| **Host Validation** | `TrustedHostMiddleware` | `ALLOWED_HOSTS` |
| **Security Headers** | CSP, HSTS, X-Frame-Options, nosniff, etc. | Hardcoded |
| **Observability** | Request ID tracing, sensitive data redaction, structured JSON logging | `LOG_LEVEL`, `LOG_HEALTH_REQUESTS` |
| **Tracing** | OpenTelemetry (optional, via `tracing.py`) | `OTLP_ENDPOINT`, `TRACING_ENABLED` |
| **Transport Security** | MCP transport-level DNS rebinding protection | `mcp.server.transport_security` |

---

## Directory Structure

```
mcp-consulting-kit/
├── showcase-servers/
│   ├── common/                          # Shared security module
│   │   ├── security.py                  #   CORS, observability, rate limiting, auth
│   │   ├── security_baseline.py         #   Security headers + middleware baseline
│   │   ├── tracing.py                   #   OpenTelemetry distributed tracing
│   │   └── test_security_common.py      #   Tests for shared module
│   │
│   ├── business-intelligence-mcp/       # Port 8101
│   │   ├── main.py                      #   FastAPI + MCP mount
│   │   ├── mcp_tools.py                 #   MCP tool definitions
│   │   ├── db.py                        #   DB abstraction (PG/MySQL/SQLite)
│   │   ├── llm_provider.py              #   LLM abstraction (Claude/rule/local)
│   │   ├── mcp_transport.py             #   MCP transport config
│   │   ├── security.py                  #   Server-specific security
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── api-integration-hub/             # Port 8102
│   │   ├── main.py                      #   FastAPI + MCP mount
│   │   ├── mcp_tools.py                 #   Slack/GitHub/Stripe tools
│   │   ├── mcp_transport.py             #   MCP transport config
│   │   ├── security.py                  #   Server-specific security
│   │   ├── clients/
│   │   │   ├── slack_client.py
│   │   │   ├── github_client.py
│   │   │   ├── stripe_client.py
│   │   │   └── rate_limiter.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── content-automation-mcp/          # Port 8103
│   │   ├── main.py                      #   FastAPI + MCP mount
│   │   ├── mcp_tools.py                 #   Scraping/RSS tools
│   │   ├── mcp_transport.py             #   MCP transport config
│   │   ├── scraper.py                   #   BeautifulSoup engine
│   │   ├── security.py                  #   Server-specific security
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── github-mcp-safe/                 # Port 8105
│       ├── main.py                      #   FastAPI + lifespan-managed MCP
│       ├── mcp_tools.py                 #   GitHub MCP tools
│       ├── mcp_transport.py             #   MCP transport config
│       ├── Dockerfile
│       └── requirements.txt
│
├── intelligence_mcp.py                  # Port 8104 — Market intelligence server
├── get_intelligence.py                  # CLI script to pull daily intelligence
│
├── frontend/                            # Production UI (React + Vite)
│   ├── src/                             #   React source
│   ├── Dockerfile                       #   Nginx-based container
│   └── package.json
│
├── app/                                 # Secondary UI app
│   ├── src/
│   └── package.json
│
├── consulting-materials/                # Business/assets for consultants
│   ├── index.html                       #   Landing page
│   ├── OPERATOR-PLAYBOOK.md             #   Non-technical implementation guide
│   ├── COMPLETE-INVENTORY.md            #   Full asset inventory
│   ├── outreach-strategy.md             #   Email/LinkedIn templates
│   ├── pitch-deck-outline.md            #   17-slide deck outline
│   ├── business-model-overview.md       #   Pricing & value prop
│   ├── market-launch-plan.md            #   GTM plan
│   └── QUICK-START.md                   #   First 30-day roadmap
│
├── deploy/
│   └── nginx/
│       ├── mcp.conf                     #   Nginx reverse-proxy config
│       ├── htpasswd                     #   Basic auth credentials
│       └── mcp.new-server.snippet.conf  #   Template for adding new servers
│
├── scripts/                             # Ops automation
│   ├── launch.py                        #   Cross-platform server launcher
│   ├── sync-all.ps1 / sync-all.sh       #   Sync to remote server
│   ├── status-all.ps1 / status-all.sh   #   Health check across servers
│   ├── start-claude-mcp-tunnel.ps1      #   SSH tunnel manager
│   ├── start-claude-ready.ps1           #   Full Claude desktop prep
│   ├── harden-claude-mcp-config.ps1     #   Config hardening
│   ├── check-claude-mcp-health.ps1      #   Health verification
│   ├── monitor-mcp-stack.ps1            #   Monitoring probe
│   ├── install-mcp-monitor-task.ps1     #   Scheduled task installer
│   └── run-security-smoke.ps1           #   Security smoke test runner
│
├── docker-compose.yaml                  # Core service definitions
├── docker-compose.proxy.yaml            # Nginx proxy overlay
├── docker-compose.cloudflare.yaml       # Cloudflare tunnel overlay
├── docker-compose.cloudflare.local.yaml # Local tunnel variant
├── docker-compose.fusional.yaml         # FusionAL-specific overlay
├── nginx.conf                           # Standalone Nginx config
├── nginx-compose.yaml                   # Alternative proxy compose file
│
├── docs/                                # Documentation and runbooks
├── .github/workflows/                   # CI pipelines
├── data/bi-db/                          # BI server persistent data
├── logs/                                # Server logs
└── .hermes/                             # Hermes cron job maintenance
```

---

## Related Documents

| Document | Location |
|---|---|
| Quick Start Guide | `README.md` |
| Operator Playbook (non-technical) | `consulting-materials/OPERATOR-PLAYBOOK.md` |
| Complete Asset Inventory | `consulting-materials/COMPLETE-INVENTORY.md` |
| Engagement → Feature Intake Loop | `docs/ENGAGEMENT-FEATURE-INTAKE-LOOP.md` |
| Cloudflare Tunnel Setup | `docs/CLOUDFLARE-TUNNEL-SETUP.md` |
| t3610 Ops Hardening Runbook | `docs/T3610-MCP-OPS-HARDENING-RUNBOOK.md` |
| New Server Cutover Checklist | `docs/NEW-SERVER-CUTOVER-CHECKLIST.md` |
| Execution 30-Day Plan | `docs/EXECUTION-30D-PLAN.md` |
| Roadmap | `ROADMAP.md` |
| Maintenance Log | `MAINTENANCE.md` |
| Security Hardening | `showcase-servers/common/SECURITY-HARDENING.md` |
