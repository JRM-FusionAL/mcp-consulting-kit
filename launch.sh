#!/usr/bin/env bash
# launch.sh - Start all mcp-consulting-kit servers on Linux / macOS
# Usage:
#   ./launch.sh          # start all servers (background, logs to ./logs/)
#   ./launch.sh stop     # stop all servers
#   ./launch.sh status   # health check all servers
#   ./launch.sh logs     # tail all logs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHOWCASE="$SCRIPT_DIR/showcase-servers"
LOG_DIR="$SCRIPT_DIR/logs"
PID_FILE="$SCRIPT_DIR/.server-pids"

SERVERS=(
    "business-intelligence-mcp:8101"
    "api-integration-hub:8102"
    "content-automation-mcp:8103"
)

# Find python3
PYTHON=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON" ]; then
    echo "❌ Python 3 not found. Install from https://python.org"
    exit 1
fi

start_servers() {
    mkdir -p "$LOG_DIR"
    > "$PID_FILE"

    echo ""
    echo "🚀 Starting mcp-consulting-kit servers"
    echo "   Platform: $(uname -s) | Python: $PYTHON"
    echo "   Repo: $SCRIPT_DIR"
    echo ""

    for entry in "${SERVERS[@]}"; do
        NAME="${entry%%:*}"
        PORT="${entry##*:}"
        DIR="$SHOWCASE/$NAME"
        LOG="$LOG_DIR/$NAME.log"

        if [ ! -d "$DIR" ]; then
            echo "  ⚠️  Not found: $DIR"
            continue
        fi

        # Load .env if present
        if [ -f "$DIR/.env" ]; then
            set -a
            source "$DIR/.env"
            set +a
        fi

        cd "$DIR"
        $PYTHON -m uvicorn main:app \
            --host 0.0.0.0 \
            --port "$PORT" \
            --reload \
            > "$LOG" 2>&1 &

        PID=$!
        echo "$PID" >> "$PID_FILE"
        echo "  ✅ $NAME → http://localhost:$PORT (pid $PID, log: logs/$NAME.log)"
        cd "$SCRIPT_DIR"
        sleep 0.3
    done

    echo ""
    echo "⏳ Waiting for servers to come up..."
    sleep 4
    check_status
    echo ""
    echo "Press Ctrl+C to stop all servers"
    echo ""

    # Wait and trap Ctrl+C
    trap stop_servers INT TERM
    wait
}

stop_servers() {
    echo ""
    echo "Stopping servers..."
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            kill "$pid" 2>/dev/null && echo "  Stopped pid $pid" || true
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    # Also kill any stray uvicorn processes for these ports
    pkill -f "uvicorn main:app" 2>/dev/null || true
    echo "✅ All servers stopped"
}

check_status() {
    echo "Server health:"
    for entry in "${SERVERS[@]}"; do
        NAME="${entry%%:*}"
        PORT="${entry##*:}"
        if curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
            echo "  ✅ $NAME → http://localhost:$PORT/health"
        else
            echo "  ❌ $NAME → http://localhost:$PORT/health (not responding)"
        fi
    done
}

tail_logs() {
    mkdir -p "$LOG_DIR"
    echo "Tailing logs (Ctrl+C to stop)..."
    tail -f "$LOG_DIR"/*.log 2>/dev/null || echo "No log files yet. Start servers first."
}

case "${1:-start}" in
    start)   start_servers ;;
    stop)    stop_servers ;;
    status)  check_status ;;
    logs)    tail_logs ;;
    restart) stop_servers; sleep 1; start_servers ;;
    *)
        echo "Usage: $0 {start|stop|status|logs|restart}"
        exit 1
        ;;
esac
