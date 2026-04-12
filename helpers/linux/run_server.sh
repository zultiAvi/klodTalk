#!/usr/bin/env bash
#
# Run the klodTalk WebSocket server using the project's venv.
#
# Usage:
#   ./helpers/linux/run_server.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
SERVER="$PROJECT_ROOT/server/server.py"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Create it with:  python3 -m venv .venv && .venv/bin/pip install -r server/requirements.txt"
    exit 1
fi

while true; do
    "$VENV_PYTHON" "$SERVER" "$@"
    EXIT_CODE=$?
    echo "[run_server] Server exited with code $EXIT_CODE. Restarting in 3 seconds..."
    sleep 3
done
