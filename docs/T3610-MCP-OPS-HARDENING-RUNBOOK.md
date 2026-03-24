# T3610 MCP Ops Hardening Runbook

## Purpose

Keep public MCP endpoints stable for Smithery users and future clients.

This runbook is for the production stack on t3610:
- gateway.fusional.dev -> FusionAL (8089)
- bi.fusional.dev -> business-intelligence-mcp (8101)
- api.fusional.dev -> api-integration-hub (8102)
- content.fusional.dev -> content-automation-mcp (8103)
- intel.fusional.dev -> intelligence-mcp (8104)

---

## SLO Targets

- Availability target per public endpoint: 99.5% monthly
- p95 latency target:
  - /health <= 500 ms
  - MCP initialize <= 1500 ms
- Error rate target: < 2% 5xx over 15 minutes

---

## Alert Thresholds

Trigger an alert when any condition is true.

### P1 (page now)
- Any public endpoint is down for 5 consecutive minutes
- Cloudflare tunnel is down for 2 consecutive minutes
- 5xx error rate >= 10% over 5 minutes
- Host disk usage >= 95%
- Host memory usage >= 95% for 10 minutes

### P2 (action within 1 hour)
- Endpoint health check fails for 2 consecutive checks
- 5xx error rate >= 2% over 15 minutes
- p95 MCP initialize > 1500 ms for 15 minutes
- Host CPU >= 90% for 15 minutes
- Host memory >= 85% for 15 minutes
- Host disk >= 85%

### P3 (same-day cleanup)
- cloudflared process restarted unexpectedly
- single container restart observed
- error bursts that self-recover in under 2 minutes

---

## Daily Checklist (10-15 minutes)

1. Verify endpoint health
   - https://gateway.fusional.dev/health
   - https://bi.fusional.dev/health
   - https://api.fusional.dev/health
   - https://content.fusional.dev/health
   - https://intel.fusional.dev/health

2. Verify container state on t3610
   - All MCP containers Up
   - No frequent restart loops

3. Verify cloudflared process and log freshness
   - Process running
   - No repeated connection/auth errors in log

4. Verify host pressure
   - CPU, memory, disk below thresholds

5. Verify MCP tunnel workflow (Windows operator station)
   - scripts/start-claude-ready.ps1 -UseTunnel -SkipLaunchClaude -NonInteractive

---

## Weekly Checklist (30-45 minutes)

1. Confirm backup and recovery path
   - claude_desktop_config.json backup exists and restores cleanly
   - .env files present and documented in secure storage

2. Review logs for trends
   - top error signatures by service
   - endpoints with rising latency or failures

3. Security hygiene
   - rotate API keys on schedule (overlap + revoke)
   - check revoked keys are enforced
   - verify rate limit behavior on each public endpoint

4. Capacity review
   - compare weekly peak traffic vs host headroom
   - decide if any endpoint needs split-host or client isolation

5. Deployment safety
   - dry-run rollout in one service first
   - confirm rollback command and last known good tag

---

## Fast Triage Commands

Run from your Windows machine:

```powershell
# local+remote status snapshot
./scripts/status-all.ps1 -RemoteAlias t3610

# tunnel prep without launching Claude
./scripts/start-claude-ready.ps1 -UseTunnel -SkipLaunchClaude -NonInteractive

# check tunneled MCP health
./scripts/check-claude-mcp-health.ps1 -UseTunnelPorts
```

Run on t3610 via ssh:

```bash
# containers
ssh t3610 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# recent container restarts and health
ssh t3610 "docker ps -a --format '{{.Names}} {{.Status}}'"

# host pressure
ssh t3610 "df -h && free -h && uptime"

# cloudflared process and last logs
ssh t3610 "pgrep -af cloudflared"
ssh t3610 "tail -n 120 ~/.cloudflared/cloudflared.log"
```

---

## Incident Playbook

### A. Public endpoints down

1. Confirm cloudflared is up
2. Confirm target container is Up
3. Restart only the failed service container
4. Recheck /health and MCP initialize
5. If still failing, roll back to last known good image/tag

### B. High latency, no hard downtime

1. Check host CPU/memory/disk
2. Check service logs for downstream timeouts (DB/API)
3. Rate-limit noisy endpoint or key if needed
4. Restart only affected service if memory leak suspected
5. Open follow-up action in runbook notes

### C. Repeated tunnel drops

1. Inspect cloudflared log for auth/network errors
2. Restart cloudflared cleanly
3. Validate DNS/tunnel route mapping
4. If still unstable, fail over to temporary SSH tunnel workflow for operations

---

## Change Control Rules

- Never deploy all services at once unless emergency rollback required.
- Deploy one service, verify health + basic MCP call, then continue.
- Keep one rollback point available at all times (previous image/tag).
- Any change to startup/security scripts must update README and this runbook.

---

## Minimum Monitoring Stack

Use any monitor that can hit URLs and send notifications.

Required checks:
- HTTP GET /health for all public endpoints every 60s
- MCP initialize POST check every 2-5 minutes (one endpoint per cycle)
- cloudflared process alive every 60s
- host CPU/memory/disk every 60s

Recommended notification targets:
- Primary: Slack or SMS
- Secondary: email

---

## Current Operational Scope

- t3610 is production infrastructure for public listings today.
- Public Smithery traffic can reach your t3610-hosted services.
- For higher reliability, move toward per-client isolation as usage grows.
