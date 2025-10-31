#!/bin/bash
set -euo pipefail

export MCP_TRANSPORT=${MCP_TRANSPORT:-http}

uvicorn app:app --host "${UVICORN_HOST:-0.0.0.0}" --port "${UVICORN_PORT:-8000}" &
APP_PID=$!

fastmcp run MCP/mcp_server.py:mcp --transport "${MCP_TRANSPORT:-http}" --port "${MCP_PORT:-8800}" &
MCP_PID=$!

nginx -g "daemon off;" &
NGINX_PID=$!

terminate() {
    kill -TERM "$NGINX_PID" "$APP_PID" "$MCP_PID" >/dev/null 2>&1 || true
}

trap terminate INT TERM

wait -n "$APP_PID" "$MCP_PID" "$NGINX_PID"
STATUS=$?
terminate
wait >/dev/null 2>&1 || true
exit "$STATUS"
