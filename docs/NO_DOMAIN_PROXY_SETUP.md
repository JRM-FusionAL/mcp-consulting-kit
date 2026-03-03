# FusionAL MCP Proxy Setup (No Domain)

This setup adds a reverse proxy on your Ubuntu host **without a domain**.
It is designed to be safer by default:

- MCP services stay as-is
- Proxy requires basic auth
- Proxy binds to `127.0.0.1:8088` on server (not public)
- You access it via SSH tunnel or private network VPN

## Files Added

- `docker-compose.proxy.yaml`
- `docker-compose.proxy.local.yaml` (local overrides, gitignored)
- `deploy/nginx/mcp.conf`
- `deploy/nginx/.htpasswd.example`

## 1) Create proxy credentials on Ubuntu

From repo root:

```bash
sudo apt-get update
sudo apt-get install -y apache2-utils
sudo mkdir -p deploy/nginx
sudo htpasswd -cb deploy/nginx/.htpasswd mcpadmin "CHANGE_ME_STRONG_PASSWORD"
```

If you get a permissions error, ensure you are running from repo root and use `sudo`.

## 2) Start stack with proxy overlay

```bash
docker compose -f docker-compose.yaml -f docker-compose.proxy.yaml -f docker-compose.proxy.local.yaml up -d
```

If your server does not support `docker compose` (Compose v2 plugin), use:

```bash
docker-compose -f docker-compose.yaml -f docker-compose.proxy.yaml -f docker-compose.proxy.local.yaml up -d
```

Quick verify:

```bash
ls -la deploy/nginx/.htpasswd
docker-compose -f docker-compose.yaml -f docker-compose.proxy.yaml -f docker-compose.proxy.local.yaml ps
curl -u mcpadmin:CHANGE_ME_STRONG_PASSWORD http://127.0.0.1:8088/healthz
```

## 3) Create SSH tunnel from your local machine

```bash
ssh -L 8088:127.0.0.1:8088 t3610
```

Now local access points are:

- `http://localhost:8088/bi/` -> Business Intelligence MCP (`/mcp`)
- `http://localhost:8088/api/` -> API Integration Hub MCP (`/mcp`)
- `http://localhost:8088/content/` -> Content Automation MCP (`/mcp`)
- `http://localhost:8088/intel/` -> Intelligence MCP (`/mcp`)

All routes require the basic auth username/password you created.

## VS Code MCP examples

Direct to server host:

```json
{
  "servers": {
    "business-intelligence-mcp": { "type": "http", "url": "http://just2awesome:8088/bi/" },
    "api-integration-hub": { "type": "http", "url": "http://just2awesome:8088/api/" },
    "content-automation-mcp": { "type": "http", "url": "http://just2awesome:8088/content/" },
    "Intelligence_mcp": { "type": "http", "url": "http://just2awesome:8088/intel/" }
  }
}
```

If using an SSH tunnel, replace `just2awesome` with `localhost`.

## Important note

Because this is no-domain and uses HTTP, keep it private (SSH tunnel or VPN). If you expose it publicly, add TLS via a domain or private PKI first.
