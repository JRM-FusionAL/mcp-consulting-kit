# Cloudflare Tunnel Setup (for MCP Proxy)

This exposes your MCP proxy securely over HTTPS without opening inbound firewall ports.

## What This Assumes

- Your MCP services are already running behind local proxy on `mcp-proxy` (port 8080 in container, host `127.0.0.1:8088`).
- You have a Cloudflare account and a domain managed in Cloudflare DNS.

## Files Used

- `docker-compose.proxy.yaml`
- `docker-compose.cloudflare.yaml`
- `deploy/nginx/mcp.conf`

## 1) Create Cloudflare Tunnel + Token

In Cloudflare Zero Trust:

1. Go to **Networks → Tunnels**
2. Create a tunnel (example name: `mcp-gateway`)
3. Add public hostname(s), for example:
   - `mcp.yourdomain.com` → `http://mcp-proxy:8080`
4. Copy the generated **Tunnel token**

## 2) Create Local Env File (Not Committed)

Create `docker-compose.cloudflare.local.yaml` in repo root:

```yaml
services:
  cloudflared:
    environment:
      - CF_TUNNEL_TOKEN=YOUR_TUNNEL_TOKEN_HERE
```

## 3) Start Stack with Proxy + Tunnel

```bash
docker compose \
  -f docker-compose.yaml \
  -f docker-compose.proxy.yaml \
  -f docker-compose.cloudflare.yaml \
  -f docker-compose.cloudflare.local.yaml \
  up -d
```

## 4) Verify

```bash
curl -u mcpadmin:CHANGE_ME_STRONG_PASSWORD https://mcp.yourdomain.com/healthz
```

If health returns `ok`, tunnel routing is working.

## 5) Client Endpoint Examples

Use your Cloudflare hostname in MCP clients:

- `https://mcp.yourdomain.com/bi/`
- `https://mcp.yourdomain.com/api/`
- `https://mcp.yourdomain.com/content/`
- `https://mcp.yourdomain.com/intel/`

## Security Recommendations (Important)

- Keep basic auth in `deploy/nginx/.htpasswd` enabled.
- Add Cloudflare Access policy (email allowlist or IdP groups) for `mcp.yourdomain.com`.
- Keep services private; only `cloudflared` should be internet-facing.
- Rotate tunnel token if leaked.

## Troubleshooting

### `cloudflared` container restarts continuously

- Token is invalid/expired. Regenerate token and update `docker-compose.cloudflare.local.yaml`.

### 502/Bad Gateway from hostname

- `mcp-proxy` not healthy or wrong origin target. Confirm `mcp-proxy` is up and hostname route points to `http://mcp-proxy:8080`.

### Auth prompts loop

- Verify `.htpasswd` file exists and mounted correctly in proxy container.

## Optional: Quick Temporary URL (No Domain)

If you need a fast test URL, use Cloudflare quick tunnel from host:

```bash
cloudflared tunnel --url http://127.0.0.1:8088
```

Use this only for short-lived testing.
