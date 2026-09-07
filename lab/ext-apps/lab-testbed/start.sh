#!/bin/bash
# lab-testbed/start.sh — start all lab services
set -e
cd "$(dirname "$0")/.."

echo "=== Stopping old services ==="
for p in 8090 8091 3001 9999; do fuser -k $p/tcp 2>/dev/null || true; done
sleep 1

echo "=== Starting exfil receiver (9999) ==="
node lab-testbed/server/receiver.mjs &

echo "=== Starting lab MCP server (3001) ==="
node lab-testbed/server/server.mjs &

echo "=== Starting host-policy (8090/8091) with policy OFF ==="
HOST_PORT=8090 SANDBOX_PORT=8091 SERVERS='["http://localhost:3001/mcp"]' npx tsx lab-testbed/host-policy/serve.ts &

echo "=== Waiting for services ==="
sleep 5

echo "=== Health checks ==="
for p in 3001 8090 8091 9999; do
  if lsof -i :$p -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  port $p: UP"
  else
    echo "  port $p: DOWN"
  fi
done
echo "=== Done ==="
