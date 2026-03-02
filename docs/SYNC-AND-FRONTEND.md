# Sync + Frontend Ops (Windows, macOS, Linux)

This guide keeps all three repositories in sync between your local machine and server `t3610`:

- `mcp-consulting-kit`
- `FusionAL`
- `Christopher-AI`

It also documents the production frontend workflow.

---

## 1) Cross-platform sync scripts

### Windows (PowerShell)

From `mcp-consulting-kit`:

```powershell
./scripts/sync-all.ps1 -RemoteAlias t3610 -RemoteBase /home/jrm_fusional/Projects
```

Dry run:

```powershell
./scripts/sync-all.ps1 -DryRun
```

Sync + rebuild remote docker workloads:

```powershell
./scripts/sync-all.ps1 -RestartDocker
```

### macOS / Linux

```bash
chmod +x ./scripts/sync-all.sh
./scripts/sync-all.sh --remote t3610 --remote-base /home/jrm_fusional/Projects
```

Dry run:

```bash
./scripts/sync-all.sh --dry-run
```

Sync + rebuild remote docker workloads:

```bash
./scripts/sync-all.sh --restart-docker
```

---

## 2) Remote prerequisites (`t3610`)

- SSH alias `t3610` configured in `~/.ssh/config`
- `docker` + `docker compose` installed on remote
- Base path exists or is creatable: `/home/jrm_fusional/Projects`

Optional but recommended:
- `rsync` installed (used automatically by `sync-all.sh`)

---

## 3) Production frontend

Frontend source is in `frontend/`.

Install:

```bash
cd frontend
npm install
```

Local dev:

```bash
npm run dev
```

Production build:

```bash
npm run build
```

Preview built assets:

```bash
npm run preview
```

The production static output is written to:

- `frontend/dist`

---

## 4) Frontend environment

The app defaults to local service URLs:

- `http://localhost:8101`
- `http://localhost:8102`
- `http://localhost:8103`
- `http://localhost:8089`

To override, set in `frontend/.env`:

```bash
VITE_BI_BASE_URL=https://your-bi-host
VITE_API_HUB_BASE_URL=https://your-api-host
VITE_CONTENT_BASE_URL=https://your-content-host
VITE_FUSIONAL_BASE_URL=https://your-fusional-host
```

---

## 5) Recommended deploy sequence

1. Run sync script (`sync-all.ps1` or `sync-all.sh`)
2. Restart remote docker (`-RestartDocker` or `--restart-docker`)
3. Build frontend (`npm run build`)
4. Deploy `frontend/dist` to your hosting provider

---

## 6) One-command status check

Check local + remote service health together:

```powershell
./scripts/status-all.ps1 -RemoteAlias t3610
```

```bash
./scripts/status-all.sh --remote t3610
```

Ports checked: `8101`, `8102`, `8103`, and FusionAL on `8089` or `8009`.
