# New Server Cutover Checklist (Fast Path)

Use this when the new Claude-built server is ready to land.

## 1) Add Runtime Files

- Add server implementation file (example: `new_server.py`)
- Add `Dockerfile.newserver`
- Add requirements if needed

## 2) Add Compose Service

Option A (direct): add service into `docker-compose.yaml`

Option B (recommended for fast testing): copy `docker-compose.next-server.example.yaml` to:

- `docker-compose.next-server.local.yaml`

Then run with overlay:

```bash
docker compose -f docker-compose.yaml -f docker-compose.next-server.local.yaml up -d
```

## 3) Add Proxy Route

- Copy snippet from `deploy/nginx/mcp.new-server.snippet.conf`
- Add to `deploy/nginx/mcp.conf`
- Route convention: `/new/` -> `new-server-mcp:8105/mcp/`

Restart proxy stack after change.

## 4) Add Client Endpoint

Use endpoint:

- `http://just2awesome:8088/new/` (proxy)
- `https://mcp.yourdomain.com/new/` (Cloudflare tunnel)

## 5) Health + Smoke Test

- Container up and healthy
- Proxy route returns MCP handshake
- Basic tool call succeeds from client

## 6) Docs + GTM Sync

- Add server summary to `README.md`
- Add route to `docs/NO_DOMAIN_PROXY_SETUP.md`
- Add route to `docs/CLOUDFLARE-TUNNEL-SETUP.md`
- Add one-line business outcome to outreach/demo script

## 7) Naming Standard

- Container: `new-server-mcp`
- Port: `8105`
- Proxy route: `/new/`
- Image Dockerfile: `Dockerfile.newserver`
