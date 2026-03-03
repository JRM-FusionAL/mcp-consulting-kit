# New Server Intake Notes

## Source Checked

- `c:\Users\puddi\Downloads\FusionAL Project Files\Intelligence_mcp\intelligence_mcp.py`
- `c:\Users\puddi\Downloads\FusionAL Project Files\Intelligence_mcp\intelligence_mcp_deploy.yml`

## What’s New / Status

- New server candidate identified: `intelligence_mcp` (port `8104`)
- It is already integrated into `mcp-consulting-kit` as:
  - `intelligence_mcp.py`
  - `Dockerfile.intelligence`
  - `docker-compose.yaml` (`intelligence-mcp` service)
  - proxy route `/intel/` in `deploy/nginx/mcp.conf`
- Build context has been corrected to repo-local path in compose.

## Delta Observed

- Repo version of `intelligence_mcp.py` is ahead of the Downloads copy:
  - includes HTTP transport mount via Starlette + Uvicorn entrypoint
  - includes `os` import and runtime port env handling

## Integration Checklist for the Next Server

When your next server is ready, follow this pattern:

1. Add `new_server.py` at repo root or under a dedicated service folder
2. Add `Dockerfile.<server>`
3. Add service in `docker-compose.yaml`
4. Add proxy route in `deploy/nginx/mcp.conf` (if proxied)
5. Add route docs to `docs/NO_DOMAIN_PROXY_SETUP.md` and `docs/CLOUDFLARE-TUNNEL-SETUP.md`
6. Add health/status mention in launcher docs if needed

## Suggestion for Next Step

Use naming convention:

- container: `new-server-mcp`
- route: `/new/`
- port: next free (`8105`)

This keeps consistency with current stack (`/bi`, `/api`, `/content`, `/intel`).
