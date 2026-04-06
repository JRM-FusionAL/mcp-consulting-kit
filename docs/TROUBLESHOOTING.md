# MCP Consulting Kit — Troubleshooting Matrix

Symptom → Probable Cause → Fix for the four main problem domains:
**Setup · Connectivity · Authentication · Runtime**

Use the [Quick Reference](#quick-reference) table for a fast scan, then jump to the matching section for diagnosis commands and step-by-step fixes.
For issues that remain unresolved after following the fix path, see [Escalation Criteria](#escalation-criteria).

---

## Quick Reference

| # | Category | Symptom | Probable Cause | Jump to |
|---|----------|---------|----------------|---------|
| S-1 | Setup | Docker build fails / `not found` errors | Missing base image or broken network | [S-1](#s-1-docker-build-fails) |
| S-2 | Setup | `uvicorn: command not found` or `ModuleNotFoundError` | Dependencies not installed | [S-2](#s-2-missing-python-dependencies) |
| S-3 | Setup | Server starts but `.env` values are ignored | `.env` file in wrong directory or not loaded | [S-3](#s-3-env-file-not-loaded) |
| S-4 | Setup | Claude Desktop shows no MCP tools | `claude_desktop_config.json` misconfigured | [S-4](#s-4-claude-desktop-shows-no-mcp-tools) |
| S-5 | Setup | Port already in use (`Address already in use`) | Stale container or local process | [S-5](#s-5-port-already-in-use) |
| C-1 | Connectivity | `curl http://localhost:810x/health` fails | Container not running or wrong port | [C-1](#c-1-health-check-fails-locally) |
| C-2 | Connectivity | Public endpoint unreachable (Cloudflare tunnel) | `cloudflared` stopped or misconfigured | [C-2](#c-2-public-endpoint-unreachable-via-cloudflare-tunnel) |
| C-3 | Connectivity | Database connection error on BI server | Wrong `DB_URL` or firewall | [C-3](#c-3-database-connection-error-bi-server) |
| C-4 | Connectivity | Slack / GitHub / Stripe calls silently fail | Missing or incorrect third-party token | [C-4](#c-4-third-party-api-calls-silently-fail-api-hub) |
| C-5 | Connectivity | CORS errors in browser / frontend | `ALLOWED_ORIGINS` not set correctly | [C-5](#c-5-cors-errors) |
| A-1 | Auth | `401 Invalid API key` on every request | Wrong or missing `X-API-Key` header | [A-1](#a-1-401-invalid-api-key) |
| A-2 | Auth | `500 API_KEY is not configured` | Neither `API_KEY` nor `API_KEYS` set in env | [A-2](#a-2-500-api_key-is-not-configured) |
| A-3 | Auth | Valid key suddenly returns `401` | Key was revoked via `REVOKED_API_KEYS` | [A-3](#a-3-valid-key-returns-401-after-rotation) |
| A-4 | Auth | `429 Too Many Requests` | Rate limit exceeded | [A-4](#a-4-429-too-many-requests) |
| R-1 | Runtime | BI server returns `SQL generation failed` | LLM provider error or bad `ANTHROPIC_API_KEY` | [R-1](#r-1-bi-server-sql-generation-failed) |
| R-2 | Runtime | BI server returns `SQL safety check failed` | Query contains write / DDL operations | [R-2](#r-2-bi-server-sql-safety-check-failed) |
| R-3 | Runtime | Content server returns empty scrape results | Target site blocks bots or page structure changed | [R-3](#r-3-content-server-empty-scrape-results) |
| R-4 | Runtime | Redis warnings in logs, rate limiting behaves oddly | `REDIS_URL` unreachable; fallback to in-memory | [R-4](#r-4-redis-unavailable--rate-limit-behaves-oddly) |
| R-5 | Runtime | Container crash-loops (`Restarting` in `docker ps`) | Fatal startup error (missing env, import error) | [R-5](#r-5-container-crash-loops) |
| R-6 | Runtime | High latency / timeouts on MCP calls | Host resource pressure or downstream API slow | [R-6](#r-6-high-latency--timeouts) |

---

## Setup Issues

### S-1 Docker Build Fails

**Symptom**
```
ERROR [internal] load metadata for docker.io/library/python:3.11-slim
failed to solve: ...
```
or missing `apt` packages during build.

**Probable Cause**
- No internet access from the build host
- Docker Hub rate-limit hit
- Stale build cache referencing a deleted layer

**Diagnosis**
```bash
# Confirm internet access from Docker
docker run --rm alpine ping -c 3 8.8.8.8

# Check Docker login status (for pull-rate limits)
docker login

# See full build output
docker build --no-cache -t bi-mcp-showcase showcase-servers/business-intelligence-mcp 2>&1 | tail -30
```

**Fix**
1. If no internet: ensure Docker has network access; for air-gapped environments, pre-pull the base image and `docker save` / `docker load` it.
2. If rate-limited: `docker login` with a Docker Hub account (free tier gets higher pull limits).
3. If stale cache: add `--no-cache` flag to the build command.
4. On Windows, ensure Docker Desktop → Settings → Resources → WSL2 has enough memory (≥ 4 GB recommended).

---

### S-2 Missing Python Dependencies

**Symptom**
```
uvicorn: command not found
ModuleNotFoundError: No module named 'fastapi'
```

**Probable Cause**
Dependencies were not installed, or the wrong virtual environment is active.

**Diagnosis**
```bash
# Inside the server directory
python --version            # should be 3.11+
pip show fastapi uvicorn    # confirms installation
```

**Fix**
```bash
# Inside each server directory
pip install -r requirements.txt

# Or for the full stack
pip install fastapi uvicorn[standard] python-dotenv pydantic requests \
            beautifulsoup4 feedparser lxml sqlalchemy "mcp[cli]"
```
If using a virtual environment, activate it first:
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows PowerShell
pip install -r requirements.txt
```

---

### S-3 `.env` File Not Loaded

**Symptom**
Server starts but env vars appear blank (e.g., `DB_URL` is `None`, auth returns 500).

**Probable Cause**
- `.env` file is in the repo root instead of the server directory
- Running `uvicorn` from a different working directory
- Using `docker run` without `--env-file`

**Diagnosis**
```bash
# Confirm .env is in the server directory
ls -la showcase-servers/business-intelligence-mcp/.env

# Check loaded vars inside a running container
docker exec <container_id> env | grep -E "API_KEY|DB_URL"
```

**Fix**
1. Place `.env` in the same directory as `main.py` for each server.
2. Run `uvicorn` from inside the server directory:
   ```bash
   cd showcase-servers/business-intelligence-mcp
   uvicorn main:app --host 0.0.0.0 --port 8101
   ```
3. For Docker, pass the env file explicitly:
   ```bash
   docker run --env-file .env -p 8101:8101 bi-mcp-showcase
   ```

---

### S-4 Claude Desktop Shows No MCP Tools

**Symptom**
Claude Desktop opens but no custom tools appear; no errors shown.

**Probable Cause**
- `claude_desktop_config.json` is missing or malformed
- MCP server URL or port is wrong in the config
- Server is not running when Claude Desktop starts

**Diagnosis**
```powershell
# Windows — open config file
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```
```bash
# macOS/Linux
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Expected structure:
```json
{
  "mcpServers": {
    "business-intelligence": {
      "url": "http://localhost:8101",
      "headers": { "X-API-Key": "your-api-key-here" }
    }
  }
}
```

**Fix**
1. Verify the server is running: `curl http://localhost:8101/health`
2. Ensure the port in the config matches the running server.
3. After editing the config, **restart Claude Desktop** for changes to take effect.
4. Check the Claude Desktop logs for MCP errors:
   ```powershell
   # Windows
   Get-Content "$env:APPDATA\Claude\logs\mcp.log" -Tail 50
   ```

---

### S-5 Port Already in Use

**Symptom**
```
ERROR: [Errno 98] Address already in use
```

**Probable Cause**
A previous container or process is still bound to the port.

**Diagnosis**
```bash
# Find what is using port 8101
lsof -i :8101            # Linux/macOS
netstat -ano | findstr 8101  # Windows PowerShell

# List running containers
docker ps
```

**Fix**
```bash
# Stop the conflicting container
docker stop <container_id>

# Or kill the local process (Linux/macOS)
kill $(lsof -ti :8101)

# Start fresh
docker run --env-file .env -p 8101:8101 bi-mcp-showcase
```

---

## Connectivity Issues

### C-1 Health Check Fails Locally

**Symptom**
```
curl: (7) Failed to connect to localhost port 8101: Connection refused
```

**Probable Cause**
- Container / server is not running
- Server started on a different port
- Docker port mapping not applied

**Diagnosis**
```bash
# Check running containers and their port mappings
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Check for recent crash
docker ps -a --format '{{.Names}} {{.Status}}'

# View logs of stopped container
docker logs <container_id> --tail 50
```

**Fix**
1. If container is absent: start it with `docker run --env-file .env -p 8101:8101 bi-mcp-showcase`.
2. If container shows `Exited`: fix the root cause from logs (see [R-5](#r-5-container-crash-loops)) then restart.
3. If wrong port: rebuild the config or override with `-e PORT=8101`.

---

### C-2 Public Endpoint Unreachable via Cloudflare Tunnel

**Symptom**
`https://bi.fusional.dev/health` returns 502/503 or times out.

**Probable Cause**
- `cloudflared` process has stopped
- Tunnel authentication token expired
- Container is up locally but the tunnel is broken

**Diagnosis**
```bash
# On the host (t3610 or your server)
pgrep -af cloudflared                              # confirm process is running
tail -n 80 ~/.cloudflared/cloudflared.log          # look for auth/connection errors

# Local container health (baseline)
curl http://localhost:8101/health
```

**Fix**
1. Restart cloudflared:
   ```bash
   pkill cloudflared
   cloudflared tunnel run <tunnel-name> &
   ```
2. If auth error: re-authenticate with `cloudflared tunnel login`.
3. Verify tunnel route: `cloudflared tunnel route list`.
4. Refer to [CLOUDFLARE-TUNNEL-SETUP.md](CLOUDFLARE-TUNNEL-SETUP.md) for full setup steps.
5. As a temporary workaround, use an SSH tunnel:
   ```bash
   ssh -L 8101:localhost:8101 user@t3610
   ```

---

### C-3 Database Connection Error (BI Server)

**Symptom**
```json
{"detail": "Database connection failed"}
```
or logs show `sqlalchemy.exc.OperationalError`.

**Probable Cause**
- `DB_URL` is incorrect or missing
- Database host is unreachable (firewall, VPN required)
- Credentials expired

**Diagnosis**
```bash
# Check the env var is set
docker exec <container_id> env | grep DB_URL

# Test connectivity to DB host directly
docker exec <container_id> python -c \
  "from sqlalchemy import create_engine, text; e=create_engine('$DB_URL'); print(e.connect().execute(text('SELECT 1')).fetchone())"
```

**Fix**
1. Correct `DB_URL` format examples:
   - PostgreSQL: `postgresql+psycopg2://user:pass@host:5432/dbname`
   - MySQL: `mysql+pymysql://user:pass@host:3306/dbname`
   - SQLite: `sqlite:///./data.db`
2. Ensure the DB host is accessible from the container network.
3. Update `.env` then restart the container.

---

### C-4 Third-Party API Calls Silently Fail (API Hub)

**Symptom**
Slack messages are not sent, GitHub issues not created, or Stripe lookups return empty results — no error surfaced to Claude.

**Probable Cause**
- Missing or expired `SLACK_BOT_TOKEN`, `GITHUB_TOKEN`, or `STRIPE_API_KEY`
- Incorrect token scope (bot not added to the channel, token lacks write permission)

**Diagnosis**
```bash
# Confirm tokens are loaded
docker exec <container_id> env | grep -E "SLACK|GITHUB|STRIPE"

# Test Slack token directly
curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  https://slack.com/api/auth.test | python3 -m json.tool

# Test GitHub token
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user | python3 -m json.tool
```

**Fix**
1. Re-generate tokens with the correct scopes:
   - Slack: `chat:write`, `channels:read`, `channels:history`
   - GitHub: `repo` scope for private repos, `public_repo` for public
   - Stripe: use a restricted key with only the required permissions
2. Update `.env` and restart the container.
3. For Slack: ensure the bot is invited to the target channel (`/invite @bot-name`).

---

### C-5 CORS Errors

**Symptom**
Browser console shows:
```
Access to fetch at 'http://localhost:8101/nl-query' from origin 'http://myapp.local' has been blocked by CORS policy
```

**Probable Cause**
`ALLOWED_ORIGINS` does not include the requesting origin.
Wildcard (`*`) origins are explicitly rejected by the security middleware.

**Diagnosis**
```bash
docker exec <container_id> env | grep ALLOWED_ORIGINS
```

**Fix**
Add your frontend origin to `.env` (no trailing slash, no wildcards):
```
ALLOWED_ORIGINS=http://localhost:3000,https://myapp.example.com
```
Restart the container for the change to take effect.

---

## Authentication Issues

### A-1 `401 Invalid API Key`

**Symptom**
Every POST request returns:
```json
{"detail": "Invalid API key"}
```

**Probable Cause**
- `X-API-Key` header is absent from the request
- The key value does not match any key in `API_KEYS` / `API_KEY`
- Key contains extra whitespace

**Diagnosis**
```bash
# Confirm the key is accepted
curl -s -X POST http://localhost:8101/nl-query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -d '{"query":"list tables"}'

# Confirm what keys are configured (non-prod only)
docker exec <container_id> env | grep -E "^API_KEY"
```

**Fix**
1. Include the `X-API-Key` header on every POST request.
2. Ensure the value exactly matches one of the keys in `API_KEYS` (comma-separated) or `API_KEY`.
3. Strip any leading/trailing whitespace from the key in `.env`.

---

### A-2 `500 API_KEY is not configured`

**Symptom**
```json
{"detail": "API_KEY is not configured"}
```

**Probable Cause**
Neither `API_KEY` nor `API_KEYS` is set in the environment.

**Diagnosis**
```bash
docker exec <container_id> env | grep -E "^API_KEY"
# Expected: at least one of API_KEY or API_KEYS must be non-empty
```

**Fix**
Add to `.env`:
```
API_KEY=replace-with-a-strong-random-value
# Or for rotation support:
API_KEYS=current-key,next-key
```
Generate a secure random key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
Restart the container after updating `.env`.

---

### A-3 Valid Key Returns `401` After Rotation

**Symptom**
A key that previously worked now returns `401 Invalid API key`.

**Probable Cause**
The key was added to `REVOKED_API_KEYS` during a rotation cycle.

**Diagnosis**
```bash
docker exec <container_id> env | grep REVOKED_API_KEYS
```

**Fix**
1. **If the revocation was intentional:** update the client to use the new active key from `API_KEYS`.
2. **If the revocation was accidental:** remove the key from `REVOKED_API_KEYS` in `.env` and restart the container.
3. Follow the rotation process in [`showcase-servers/common/SECURITY-HARDENING.md`](../showcase-servers/common/SECURITY-HARDENING.md):
   - Add the new key to `API_KEYS` first (overlap period)
   - Update all clients to the new key
   - Move the old key to `REVOKED_API_KEYS`

---

### A-4 `429 Too Many Requests`

**Symptom**
```json
{"detail": "Rate limit exceeded"}
```

**Probable Cause**
The client IP has exceeded the `RATE_LIMIT_REQUESTS` threshold within `RATE_LIMIT_WINDOW_SECONDS`.
Default: 60 requests per 60 seconds.

**Diagnosis**
```bash
# Check current limits
docker exec <container_id> env | grep -E "RATE_LIMIT"

# If Redis is in use, inspect the key
redis-cli -u $REDIS_URL keys "rate_limit:*"
```

**Fix**
1. **Short-term:** wait for the window to expire (default: 60 s), then retry.
2. **Adjust limits** for legitimate high-volume clients by editing `.env`:
   ```
   RATE_LIMIT_REQUESTS=300
   RATE_LIMIT_WINDOW_SECONDS=60
   ```
3. **Distribute requests** over time instead of bursting.
4. If Redis is used and limits are not resetting, verify `REDIS_URL` connectivity (see [R-4](#r-4-redis-unavailable--rate-limit-behaves-oddly)).

---

## Runtime Issues

### R-1 BI Server: `SQL generation failed`

**Symptom**
```json
{"detail": "SQL generation failed"}
```
Logs show an Anthropic API error.

**Probable Cause**
- `ANTHROPIC_API_KEY` is missing, expired, or has insufficient quota
- `LLM_PROVIDER` is set to `local` (currently a placeholder — not implemented)
- Network connectivity to `api.anthropic.com` is blocked

**Diagnosis**
```bash
# Confirm the key is set
docker exec <container_id> env | grep -E "ANTHROPIC|LLM_PROVIDER"

# Test API key directly
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' \
  | python3 -m json.tool
```

**Fix**
1. Set a valid `ANTHROPIC_API_KEY` in `.env`.
2. Switch to the rule-based provider to avoid LLM calls entirely:
   ```
   LLM_PROVIDER=rule
   ```
   Note: the rule-based provider handles only simple `SELECT` patterns.
3. If the `local` provider is needed, implement it in `llm_provider.py` before use.
4. Confirm outbound HTTPS to `api.anthropic.com` is not blocked by a firewall.

---

### R-2 BI Server: `SQL safety check failed`

**Symptom**
```json
{"detail": "SQL safety check failed: ..."}
```

**Probable Cause**
The generated or supplied SQL contains write, DDL, or multi-statement operations that are blocked by the safety validator:
- `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`
- Multiple statements (`;` separator)
- SQL comments (`--`, `/* */`)

**Diagnosis**
Check the server logs for the rejected SQL and the specific violation rule.

**Fix**
1. Rephrase the prompt to a read-only question (e.g., "show me…" rather than "delete…").
2. For legitimate write operations, use direct database tooling outside the MCP server (the BI server is intentionally read-only).
3. If the query is safe but uses a comment for documentation, remove the comment from the query string.

---

### R-3 Content Server: Empty Scrape Results

**Symptom**
`scrape_url` or `parse_rss` returns an empty list or `{"items": []}`.

**Probable Cause**
- Target site returns a non-200 status (bot detection, geo-block, rate-limit)
- Page content is rendered by JavaScript (not in the initial HTML)
- RSS feed URL has changed or is temporarily down
- CSS selectors / XPath used by the scraper no longer match the page structure

**Diagnosis**
```bash
# Test raw HTTP response from inside the container
docker exec <container_id> curl -si "https://target-site.com" | head -30

# Check for redirect or bot challenge
docker exec <container_id> python3 -c \
  "import requests; r=requests.get('https://target-site.com', headers={'User-Agent':'Mozilla/5.0'}); print(r.status_code, len(r.text))"
```

**Fix**
1. Add a `User-Agent` header to the scraper request if blocked.
2. For JavaScript-rendered pages, consider a headless browser solution (out of scope for the current server — escalate if needed).
3. Verify the RSS URL is still valid.
4. Update the CSS selector or extraction logic in `scraper.py` to match the current page structure.

---

### R-4 Redis Unavailable / Rate Limit Behaves Oddly

**Symptom**
Logs contain:
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```
or rate limiting resets on every container restart.

**Probable Cause**
`REDIS_URL` is not set, or the Redis instance is unreachable.
The server gracefully falls back to an **in-memory** rate limiter that resets when the container restarts and is not shared across multiple instances.

**Diagnosis**
```bash
# Confirm Redis URL
docker exec <container_id> env | grep REDIS_URL

# Test Redis connectivity
docker exec <container_id> python3 -c \
  "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"
```

**Fix**
1. **Acceptable in single-instance dev:** no action needed; in-memory fallback is intentional.
2. **For production / multi-instance:** start Redis alongside the MCP stack:
   ```yaml
   # docker-compose.yaml snippet
   redis:
     image: redis:7-alpine
     ports: ["6379:6379"]
   ```
   Then set `REDIS_URL=redis://redis:6379/0` in `.env`.
3. Ensure `REDIS_URL` uses the correct hostname for the Docker network (use the service name, not `localhost`, when using Docker Compose).

---

### R-5 Container Crash-Loops

**Symptom**
`docker ps` shows `Restarting (1) X seconds ago`.

**Probable Cause**
- Fatal import error (missing dependency)
- Missing required env var causing a crash at startup
- Port conflict (less common with Docker)

**Diagnosis**
```bash
# View startup logs
docker logs <container_id> --tail 100

# Common patterns to look for:
# - "ModuleNotFoundError" → dependency missing
# - "KeyError" / "ValueError" → env var not set or wrong type
# - "Address already in use" → port conflict inside container
```

**Fix**
1. For `ModuleNotFoundError`: rebuild the image with `--no-cache` to ensure the latest `requirements.txt` is applied.
2. For missing env vars: add all required variables to `.env` and restart.
3. For any other error: fix the reported Python traceback, rebuild the image, restart.

---

### R-6 High Latency / Timeouts

**Symptom**
Requests take > 10 s or time out; Claude Desktop shows a spinner indefinitely.

**Probable Cause**
- Host CPU / memory pressure (common during LLM calls)
- Downstream API is slow (Anthropic, Slack, GitHub, Stripe, DB)
- Container has insufficient memory

**Diagnosis**
```bash
# Host resource snapshot (Linux)
top -bn1 | head -20
free -h
df -h

# Container resource usage
docker stats --no-stream

# Check downstream latency
time curl -s http://localhost:8101/health   # should be < 100 ms
```

**Fix**
1. Restart the affected container if memory is leaking.
2. Increase Docker Desktop memory allocation if running on Windows/macOS (Settings → Resources).
3. For persistent DB latency: add a connection pool timeout to `DB_URL` (e.g., `?connect_timeout=5`).
4. For Anthropic API slowness: this is upstream; consider switching to `LLM_PROVIDER=rule` as a temporary measure.
5. See also [T3610-MCP-OPS-HARDENING-RUNBOOK.md](T3610-MCP-OPS-HARDENING-RUNBOOK.md) for alert thresholds and host-pressure playbooks.

---

## Escalation Criteria

Escalate to a developer or senior operator when **any** of the following are true after completing the relevant fix path:

### Escalate Immediately (P1)

| Condition | Action |
|-----------|--------|
| Any public endpoint down for > 10 consecutive minutes | Page on-call; follow runbook [Incident A](T3610-MCP-OPS-HARDENING-RUNBOOK.md#a-public-endpoints-down) |
| `5xx` error rate ≥ 10 % over 5 minutes | Same as above |
| Possible credential compromise (key seen in logs, public repo, etc.) | Revoke key immediately via `REVOKED_API_KEYS`, rotate all keys, notify affected clients |
| Container crash-loop not resolved in 15 minutes | Escalate to developer with the full `docker logs` output |

### Escalate Within 1 Hour (P2)

| Condition | Action |
|-----------|--------|
| Health check fails intermittently (3 + consecutive failures) | Follow runbook; if unresolved, escalate with logs |
| Database connection cannot be restored after credential update | Escalate with `DB_URL` format (redact password) and network topology |
| Rate-limit bypass suspected (traffic spike with no matching client activity) | Review logs, consider temporary IP block, notify operator |

### Escalate Same Day (P3)

| Condition | Action |
|-----------|--------|
| Scraper returns empty results for ≥ 2 days on a known-good target | Log a task for a developer to update the extraction logic |
| `LLM_PROVIDER=rule` fallback in use for > 48 h (Anthropic key not restored) | Obtain new API key or approve rule-based mode as permanent |
| Redis in-memory fallback active in a multi-client deployment | Add Redis to the stack before the next client onboards |

### What to Include When Escalating

1. **Server name** and **port** (e.g., `business-intelligence-mcp`, port 8101)
2. **Exact error message or HTTP status code**
3. **Steps already attempted** (from this document)
4. **Log output** — at minimum the last 100 lines:
   ```bash
   docker logs <container_id> --tail 100 > escalation-logs.txt
   ```
5. **Environment context**: Docker/bare-metal, Windows/Linux, local/Cloudflare-tunneled
6. **Time the issue started** (UTC)

For developer help, see the [OPERATOR-PLAYBOOK.md](../consulting-materials/OPERATOR-PLAYBOOK.md#when-to-bring-in-a-freelancer) for recommended hiring channels.

---

## Useful One-Liners

```bash
# Full status snapshot (all servers)
for port in 8101 8102 8103; do echo -n "Port $port: "; curl -s http://localhost:$port/health; echo; done

# List all MCP containers and their state
docker ps -a --filter "name=mcp" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Tail logs of a running container by image name
docker logs -f $(docker ps -qf "ancestor=bi-mcp-showcase") --tail 50

# Generate a secure API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Check which process owns a port (Linux)
ss -tlnp | grep 8101

# Windows equivalent
netstat -ano | findstr :8101
```

---

*For production monitoring thresholds, alert levels, and weekly/daily checklists, see [T3610-MCP-OPS-HARDENING-RUNBOOK.md](T3610-MCP-OPS-HARDENING-RUNBOOK.md).*
*For API key rotation procedures, see [showcase-servers/common/SECURITY-HARDENING.md](../showcase-servers/common/SECURITY-HARDENING.md).*
