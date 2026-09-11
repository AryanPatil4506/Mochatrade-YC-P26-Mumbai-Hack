#!/usr/bin/env bash
# Launches the three Sentinel services as separate processes, per CLAUDE.md's
# "process isolation" enforcement layer: agent (8001), gateway (8002),
# executor (8003). Ctrl-C stops all three.
set -euo pipefail

cd "$(dirname "$0")/.."

PIDS=()
cleanup() {
    echo "Stopping services..."
    for pid in "${PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

python -m uvicorn services.executor.api:app --port 8003 --reload &
PIDS+=($!)

python -m uvicorn services.gateway.api:app --port 8002 --reload &
PIDS+=($!)

python -m uvicorn services.agent.api:app --port 8001 --reload &
PIDS+=($!)

echo "agent:8001 gateway:8002 executor:8003 running. Ctrl-C to stop."
wait
