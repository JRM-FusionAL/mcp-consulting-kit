#!/usr/bin/env bash
set -euo pipefail

REMOTE_ALIAS="t3610"
REMOTE_BASE="/home/jrm_fusional/Projects"
RESTART_DOCKER="false"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE_ALIAS="$2"
      shift 2
      ;;
    --remote-base)
      REMOTE_BASE="$2"
      shift 2
      ;;
    --restart-docker)
      RESTART_DOCKER="true"
      shift
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BASE="$(cd "$SCRIPT_DIR/../.." && pwd)"

REPOS=(
  "mcp-consulting-kit"
  "FusionAL"
  "Christopher-AI"
)

echo ""
echo "Sync plan"
echo "  Local base : $LOCAL_BASE"
echo "  Remote     : $REMOTE_ALIAS:$REMOTE_BASE"
echo "  Repos      : ${REPOS[*]}"
echo "  Dry run    : $DRY_RUN"
echo ""

sync_repo() {
  local repo="$1"
  local src="$LOCAL_BASE/$repo"

  if [[ ! -d "$src" ]]; then
    echo "[WARN] Missing repo, skipping: $src"
    return 0
  fi

  echo "[SYNC] $repo"

  if [[ "$DRY_RUN" == "true" ]]; then
    return 0
  fi

  ssh "$REMOTE_ALIAS" "mkdir -p '$REMOTE_BASE/$repo'"

  if command -v rsync >/dev/null 2>&1; then
    rsync -az --delete \
      --exclude='.git' \
      --exclude='.venv' \
      --exclude='venv' \
      --exclude='node_modules' \
      --exclude='__pycache__' \
      --exclude='.pytest_cache' \
      --exclude='dist' \
      --exclude='build' \
      "$src/" "$REMOTE_ALIAS:$REMOTE_BASE/$repo/"
  else
    tar -czf - \
      --exclude='.git' \
      --exclude='.venv' \
      --exclude='venv' \
      --exclude='node_modules' \
      --exclude='__pycache__' \
      --exclude='.pytest_cache' \
      --exclude='dist' \
      --exclude='build' \
      -C "$LOCAL_BASE" "$repo" | ssh "$REMOTE_ALIAS" "tar -xzf - -C '$REMOTE_BASE'"
  fi
}

for repo in "${REPOS[@]}"; do
  sync_repo "$repo"
done

if [[ "$RESTART_DOCKER" == "true" ]]; then
  echo ""
  echo "[REMOTE] Refreshing docker services"
  ssh "$REMOTE_ALIAS" "
set -e
if [ -f '$REMOTE_BASE/mcp-consulting-kit/docker-compose.yaml' ]; then
  cd '$REMOTE_BASE/mcp-consulting-kit'
  if docker compose version >/dev/null 2>&1; then
    docker compose up -d --build
  else
    docker-compose up -d --build
  fi
fi
if [ -f '$REMOTE_BASE/FusionAL/compose.yaml' ]; then
  cd '$REMOTE_BASE/FusionAL'
  if docker compose version >/dev/null 2>&1; then
    docker compose up -d --build
  else
    docker-compose up -d --build
  fi
fi
"
fi

echo ""
echo "Sync completed."
