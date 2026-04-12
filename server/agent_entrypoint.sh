#!/bin/bash
# KlodTalk project container entrypoint.
# Starts and idles, waiting for run_agent.sh to be called via docker exec.

# When running with --user UID:GID that doesn't match a passwd entry,
# add one so tools (git, ssh, docker, npm) work correctly.
if ! getent passwd "$(id -u)" > /dev/null 2>&1; then
    echo "agent:x:$(id -u):$(id -g)::/home/agent:/bin/bash" >> /etc/passwd
fi

# Register the docker socket GID in /etc/group so docker CLI resolves it correctly.
if [ -n "$DOCKER_GID" ] && ! getent group "$DOCKER_GID" > /dev/null 2>&1; then
    echo "docker:x:${DOCKER_GID}:" >> /etc/group
fi

echo "=== KlodTalk Project Container ==="
echo "  Project:   ${PROJECT_NAME:-unknown}"
echo "  Workspace: /workspace"
echo "  Ready at:  $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "================================="
echo ""
echo "Container is idle. Waiting for tasks via 'docker exec'..."

# Stay alive indefinitely
exec tail -f /dev/null
