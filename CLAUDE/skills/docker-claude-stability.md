# Skill: Docker Agent CLI Stability

## When to Use
When modifying `server/Dockerfile.agent`, troubleshooting agent container behavior, or dealing with unexpected Claude CLI version changes inside containers.

## Instructions

### Problem
The Claude Code CLI can silently auto-update between or during sessions inside Docker containers. This causes:
- Non-reproducible behavior across sessions
- Potential mid-session breakage if an update changes CLI flags or output format
- Difficulty debugging issues when the CLI version is a moving target

### Solution
The agent Dockerfile sets `ENV DISABLE_UPDATES=1` to prevent the Claude Code CLI from checking for or applying updates inside containers.

### Key Files
- `server/Dockerfile.agent` — Contains `ENV DISABLE_UPDATES=1` after the `npm install` of the CLI

### Updating the CLI Version
To update the CLI version in containers:
1. Edit `server/Dockerfile.agent` and change the `npm install` line (e.g., `npm install -g @anthropic-ai/claude-code@2.1.118`)
2. Rebuild the base image
3. Remove per-project images so they pick up the new base on next session

### Notes
- `DISABLE_UPDATES=1` is a Claude Code CLI environment variable that suppresses update checks
- Always test a new CLI version locally before pinning it in the Dockerfile
- Per-project images (created via `docker commit`) inherit this env var from the base image

### Source
Inspired by Claude Code CLI v2.1.118 release (github.com/anthropics/claude-code).
