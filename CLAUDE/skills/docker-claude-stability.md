---
skill_name: docker-claude-stability
triggers:
  - Modifying server/Dockerfile.agent
  - Troubleshooting agent container behavior
  - Dealing with unexpected Claude CLI version changes inside containers
summary: Pin Claude Code CLI version in Dockerfile.agent and suppress auto-updates with DISABLE_UPDATES=1.
---

# Skill: Docker Agent CLI Stability

## Quick Reference
- Version pin: `npm install -g @anthropic-ai/claude-code@2.90.0` in `server/Dockerfile.agent`
- Update suppression: `ENV DISABLE_UPDATES=1`
- Satisfies disallowedTools frontmatter (v2.1.119+) and absolute file_path in hooks

## When to Use
When modifying `server/Dockerfile.agent`, troubleshooting agent container behavior, or dealing with unexpected Claude CLI version changes inside containers.

## Instructions

### Problem
The Claude Code CLI can silently auto-update between or during sessions inside Docker containers. This causes:
- Non-reproducible behavior across sessions
- Potential mid-session breakage if an update changes CLI flags or output format
- Difficulty debugging issues when the CLI version is a moving target

### Solution
Two safeguards work together:
1. **Version pin**: `server/Dockerfile.agent` pins `npm install -g @anthropic-ai/claude-code@2.90.0` to lock the install-time version.
2. **Update suppression**: `ENV DISABLE_UPDATES=1` prevents the CLI from checking for or applying updates inside running containers.

### Pinned Version Rationale
Version 2.90.0 was chosen because it satisfies two version-gated features:
- **disallowedTools frontmatter** (requires v2.1.119+): Role files can restrict tool access via YAML frontmatter. Used by `reviewer.md`, `executor.md`, and `validator.md`.
- **Absolute file_path in PostToolUse hooks**: Earlier versions sometimes returned relative paths, breaking hook logic.

### Key Files
- `server/Dockerfile.agent` -- Contains the pinned `npm install` and `ENV DISABLE_UPDATES=1`

### Updating the CLI Version
To update the CLI version in containers:
1. Edit `server/Dockerfile.agent` and change the version in `npm install -g @anthropic-ai/claude-code@X.Y.Z`
2. Rebuild the base image
3. Remove per-project images so they pick up the new base on next session
4. Update this skill file with the new version and rationale

### Notes
- `DISABLE_UPDATES=1` is a Claude Code CLI environment variable that suppresses update checks
- Always test a new CLI version locally before pinning it in the Dockerfile
- Per-project images (created via `docker commit`) inherit this env var from the base image

### Source
Inspired by Claude Code CLI changelog (github.com/anthropics/claude-code, ~115,000 stars).
