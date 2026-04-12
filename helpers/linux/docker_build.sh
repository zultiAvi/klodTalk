#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Copy host CA bundle (includes corporate CA) into build context so the image
# can verify SSL during curl/apt steps on corporate networks.
CA_DEST="$PROJECT_ROOT/server/host-ca-certificates.crt"
cp /etc/ssl/certs/ca-certificates.crt "$CA_DEST"

docker build --network=host -f server/Dockerfile.agent -t klodtalk-agent "$PROJECT_ROOT"
EXIT_CODE=$?

rm -f "$CA_DEST"
exit $EXIT_CODE
