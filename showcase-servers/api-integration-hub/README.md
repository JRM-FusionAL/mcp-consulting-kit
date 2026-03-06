# API Integration Hub MCP

Control Slack, GitHub, and Stripe from Claude Desktop.

## Features

- Slack: send messages, list channels, search
- GitHub: create issues, list PRs, search code
- Stripe: lookup customers, charges, subscriptions

## Env vars

- `SLACK_BOT_TOKEN`
- `GITHUB_TOKEN`
- `STRIPE_API_KEY`
- `API_KEY` (required for all POST endpoints via `X-API-Key` header)
- `API_KEYS` (optional comma-separated active keys for overlap rotation)
- `REVOKED_API_KEYS` (optional comma-separated revoked key denylist)
- `ALLOWED_ORIGINS` (comma-separated, default: `http://localhost,http://127.0.0.1`)
- `RATE_LIMIT_REQUESTS` (default: `60`)
- `RATE_LIMIT_WINDOW_SECONDS` (default: `60`)
- `REDIS_URL` (optional shared limiter backend; falls back to in-memory if unavailable)
- `LOG_LEVEL` (default: `INFO`)
- `LOG_HEALTH_REQUESTS` (`true`/`false`, default: `false`)
- `SERVICE_NAME` (optional service label in logs)
- `PORT` (default 8102)

All responses include `X-Request-ID` for request tracing.
Sensitive auth/token values are redacted in structured request logs.

## Run

```bash
docker build -t api-hub-showcase .
docker run --env-file .env -p 8102:8102 api-hub-showcase
```
