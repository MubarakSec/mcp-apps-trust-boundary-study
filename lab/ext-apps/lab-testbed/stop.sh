#!/usr/bin/env bash
# Terminate lingering daemons holding testbed ports (8090, 8091, 3001, 9999)
set -e
echo "Reaping lab testbed background processes..."
for p in 8090 8091 3001 9999; do
  fuser -k -TERM $p/tcp 2>/dev/null || true
done
sleep 1
for p in 8090 8091 3001 9999; do
  if lsof -i :$p -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  port $p: still UP (killing again)"
    fuser -k -KILL $p/tcp 2>/dev/null || true
  else
    echo "  port $p: cleared"
  fi
done
echo "Done."
