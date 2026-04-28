#!/usr/bin/env bash
set -euo pipefail

REMOTE_ALIAS="t3610"
SKIP_REMOTE="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE_ALIAS="$2"
      shift 2
      ;;
    --skip-remote)
      SKIP_REMOTE="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

check_host() {
  local label="$1"
  local base="$2"

  echo ""
  echo "[$label]"
  for p in 8101 8102 8103 8104; do
    if curl -fsS --max-time 5 "http://${base}:${p}/health" >/dev/null; then
      echo "  port ${p}: OK"
    else
      echo "  port ${p}: DOWN"
    fi
  done

  if curl -fsS --max-time 5 "http://${base}:8089/health" >/dev/null; then
    echo "  FusionAL: OK on port 8089"
  elif curl -fsS --max-time 5 "http://${base}:8009/health" >/dev/null; then
    echo "  FusionAL: OK on port 8009"
  else
    echo "  FusionAL: DOWN (checked 8089 and 8009)"
  fi
}

check_host "LOCAL" "127.0.0.1"

if [[ "$SKIP_REMOTE" != "true" ]]; then
  echo ""
  echo "[REMOTE:${REMOTE_ALIAS}]"
  ssh "$REMOTE_ALIAS" 'for p in 8101 8102 8103 8104; do printf "  port %s: " "$p"; curl -fsS --max-time 5 "http://127.0.0.1:${p}/health" >/dev/null && echo OK || echo DOWN; done; if curl -fsS --max-time 5 "http://127.0.0.1:8089/health" >/dev/null; then echo "  FusionAL: OK on port 8089"; elif curl -fsS --max-time 5 "http://127.0.0.1:8009/health" >/dev/null; then echo "  FusionAL: OK on port 8009"; else echo "  FusionAL: DOWN (checked 8089 and 8009)"; fi'
fi
