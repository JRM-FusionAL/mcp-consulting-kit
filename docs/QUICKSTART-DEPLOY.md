# Deploy in Under 15 Minutes — Quick-Start Guide

This guide gets all three showcase MCP servers running on a fresh machine in **≤ 15 minutes**.  
It covers local development setup (no cloud provider required).

> **Audience:** Technical buyers / operators evaluating the MCP Consulting Kit.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone & enter the repository](#2-clone--enter-the-repository)
3. [Run the deploy script](#3-run-the-deploy-script)
4. [Verify the servers are up](#4-verify-the-servers-up)
5. [Make your first authenticated request](#5-make-your-first-authenticated-request)
6. [Next steps](#6-next-steps)
7. [Troubleshooting — top 5 failure modes](#7-troubleshooting--top-5-failure-modes)

---

## 1. Prerequisites

Install these tools before you begin. The deploy script will validate each one.

| Tool | Minimum version | Install |
|---|---|---|
| **Git** | 2.x | <https://git-scm.com/downloads> |
| **Python** | **3.11+** | <https://python.org/downloads/> |
| **pip** | bundled with Python | `python -m ensurepip --upgrade` |
| **curl** | any (health checks) | pre-installed on macOS / Linux / Windows 10+ |
| **Docker + Compose** | Docker 24+ | <https://docs.docker.com/get-docker/> *(only if using `--docker` flag)* |

> **Windows users:** all commands below work in **PowerShell 7+**.  
> Run `winget install Microsoft.PowerShell` if you need to upgrade.

Quick prerequisite check (no changes made):

```bash
# Linux / macOS
./scripts/deploy.sh --check

# Windows PowerShell
.\scripts\deploy.ps1 -CheckOnly
```

---

## 2. Clone & enter the repository

```bash
git clone https://github.com/JRM-FusionAL/mcp-consulting-kit.git
cd mcp-consulting-kit
```

> **Existing clone?** `git pull origin main` to ensure you have the latest files.

---

## 3. Run the deploy script

Choose **one** of the two paths below.

### Path A — Local Python (recommended for first-time eval, ~5 min)

```bash
# Linux / macOS
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Windows PowerShell
.\scripts\deploy.ps1
```

What this does, step by step:

| Step | Action | Typical time |
|------|--------|-------------|
| 1 | Validate prerequisites | < 5 s |
| 2 | Auto-generate `.env` files with a random API key for each server | < 1 s |
| 3 | `pip install` dependencies for all three servers | 1–3 min |
| 4 | Start each server with `uvicorn` | < 5 s |
| 5 | Run health checks and print status | < 15 s |

The script prints your **API key** at the end — save it.

---

### Path B — Docker Compose (~8 min, includes image builds)

```bash
# Linux / macOS
./scripts/deploy.sh --docker

# Windows PowerShell
.\scripts\deploy.ps1 -Docker
```

What this does:

| Step | Action | Typical time |
|------|--------|-------------|
| 1 | Validate prerequisites (Docker required) | < 5 s |
| 2 | Auto-generate `.env` files | < 1 s |
| 3 | `docker compose up --build -d` for all three services | 4–7 min |
| 4 | Health-check each container | < 20 s |

Stop containers: `docker compose down`  
View logs: `docker compose logs -f`

---

## 4. Verify the servers are up

After the script completes, confirm all three endpoints respond:

```bash
curl http://localhost:8101/health   # Business Intelligence MCP
curl http://localhost:8102/health   # API Integration Hub
curl http://localhost:8103/health   # Content Automation MCP
```

Each should return HTTP 200 with a JSON body similar to:

```json
{"status": "ok", "service": "business-intelligence-mcp"}
```

Or use the bundled status script:

```bash
# Linux / macOS
./scripts/status-all.sh --skip-remote

# Windows PowerShell
.\scripts\status-all.ps1
```

---

## 5. Make your first authenticated request

Replace `<YOUR_API_KEY>` with the key printed by the deploy script  
(also stored in each server's `.env` as `API_KEYS=...`).

### Health (no auth required)

```bash
curl http://localhost:8101/health
```

### Natural-language SQL query (BI server)

```bash
curl -X POST http://localhost:8101/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{"query": "Show me all tables in the database"}'
```

### Scrape a URL (Content Automation server)

```bash
curl -X POST http://localhost:8103/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{"url": "https://example.com"}'
```

> **PowerShell alternative:** use `Invoke-RestMethod` or the [httpie](https://httpie.io/) CLI.

---

## 6. Next steps

| Goal | Where to look |
|------|---------------|
| Start / stop servers without re-installing | `./launch.sh` (Linux/macOS) or `.\launch-servers.ps1` (Windows) |
| Connect real databases or APIs | Edit each server's `.env` file (created in step 3) |
| Run security smoke tests | `./scripts/run-security-smoke.cmd` or `.\scripts\run-security-smoke.ps1` |
| Add FusionAL dynamic engine | `docker-compose -f docker-compose.fusional.yaml up -d` |
| Full operator playbook | `consulting-materials/OPERATOR-PLAYBOOK.md` |
| Nginx reverse-proxy setup | `docs/NO_DOMAIN_PROXY_SETUP.md` |
| Cloudflare Tunnel (public URL) | `docs/CLOUDFLARE-TUNNEL-SETUP.md` |

---

## 7. Troubleshooting — top 5 failure modes

### ❶ Port already in use — `OSError: [Errno 98] Address already in use`

**Symptom:** A server fails to start; log shows `address already in use` for port 8101, 8102, or 8103.

**Fix:**

```bash
# Find the process using the port (Linux / macOS)
lsof -i :8101        # or 8102, 8103
kill <PID>

# Windows PowerShell
netstat -ano | findstr :8101
Stop-Process -Id <PID> -Force
```

Then re-run `./scripts/deploy.sh` (or `.\scripts\deploy.ps1`).

---

### ❷ Python version too old — `SyntaxError` or import failures

**Symptom:** `pip install` works but the server crashes at startup with `SyntaxError` or missing features.

**Cause:** Python 3.10 or older is being picked up instead of 3.11+.

**Fix:**

```bash
python3 --version     # check which Python the script will use
which python3         # confirm the path
```

If multiple Python versions are installed, point to the correct one:

```bash
# Linux / macOS — use the exact binary
/usr/bin/python3.11 -m pip install -r showcase-servers/business-intelligence-mcp/requirements.txt
/usr/bin/python3.11 -m uvicorn main:app --port 8101

# Windows — use py launcher
py -3.11 -m pip install -r showcase-servers\business-intelligence-mcp\requirements.txt
```

---

### ❸ `.env` file missing — `HTTP 500 "API_KEY is not configured"`

**Symptom:** Health check returns 200 but any POST request returns HTTP 500 with body `{"detail":"API_KEY is not configured"}`.

**Cause:** The `.env` file was not created (e.g., you ran `uvicorn` manually), so neither `API_KEYS` nor `API_KEY` is set.

**Fix:**

```bash
# Check whether the file exists
ls showcase-servers/business-intelligence-mcp/.env   # Linux / macOS
dir showcase-servers\business-intelligence-mcp\.env  # Windows

# If missing, re-run the deploy script — it will create .env files automatically
./scripts/deploy.sh      # Linux / macOS
.\scripts\deploy.ps1     # Windows

# Or create the file manually:
echo "API_KEYS=my-secret-key" > showcase-servers/business-intelligence-mcp/.env
```

Restart the affected server after adding the `.env`.

---

### ❹ `pip install` fails — network / SSL errors

**Symptom:** `pip install` outputs `SSLError`, `ConnectionError`, or times out.

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Corporate proxy / firewall | Set `HTTP_PROXY` and `HTTPS_PROXY` environment variables |
| Outdated pip / certifi | `python -m pip install --upgrade pip certifi` |
| Air-gapped machine | Download a wheelhouse: `pip download -r requirements.txt -d ./wheels` on a connected machine, then `pip install --no-index --find-links ./wheels -r requirements.txt` |
| DNS failure | Try `pip install --index-url https://pypi.org/simple/ ...` |

---

### ❺ Docker image build fails — `COPY` or `RUN` error

**Symptom:** `docker compose up --build` exits with a `COPY` or `RUN pip install` error.

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Build context is wrong directory | Always run from the **repo root**: `docker compose up --build` |
| Missing `common/` directory | Confirm `showcase-servers/common/` exists: `ls showcase-servers/common/` |
| Low disk space | `docker system prune -f` to free space, then retry |
| Stale layer cache | `docker compose build --no-cache` to force a fresh build |
| Docker daemon not running | Start Docker Desktop (Windows/macOS) or `sudo systemctl start docker` (Linux) |

If the error persists, inspect the failed layer:

```bash
docker compose build --progress=plain 2>&1 | tail -40
```

---

> **Still stuck?**  
> Open an issue at <https://github.com/JRM-FusionAL/mcp-consulting-kit/issues> with the output of:
>
> ```bash
> python --version && pip --version && docker --version && git --version
> ```
