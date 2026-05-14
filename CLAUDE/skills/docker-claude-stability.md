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

### `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE` (v2.1.129+)
Claude Code v2.1.129 introduced a second, complementary environment variable:
`CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE`. Set it to `false` to instruct the CLI's
package-manager-driven update path to skip auto-updating the installed npm package
inside the container.

- **Recommended value in Dockerfile.agent**: `ENV CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=false`
- **Relationship to `DISABLE_UPDATES=1`**: keep both. `DISABLE_UPDATES=1` suppresses
  the CLI's internal update checks; `CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE=false`
  belt-and-braces the package-manager update path. Either alone may not cover all
  update triggers across CLI versions.
- **Build interaction**: the variable does not affect `npm install -g ...@X.Y.Z`
  at image-build time -- it only governs runtime auto-update behavior inside the
  running container.

### `--plugin-url` Flag (v2.1.129+)
The same release added a `--plugin-url` flag, allowing distribution of custom
Claude Code plugins from a URL when invoking the CLI. If KlodTalk ever ships its
own plugin (e.g., a KlodTalk-specific slash command), agent containers can load it
via `claude --plugin-url <url>` instead of baking the plugin into the image.

### Tracking Stable CLI Versions
The `claude-agent-sdk-python` release cadence is a reliable proxy for stable
Claude Code CLI versions: the SDK is pinned to a tested CLI version at each
release, so its release notes are a good signal for when to bump the version
pinned in `server/Dockerfile.agent`.

### Source
Inspired by Claude Code CLI changelog (github.com/anthropics/claude-code, ~115,000 stars).
- Claude Code v2.1.129 release notes (`CLAUDE_CODE_PACKAGE_MANAGER_AUTO_UPDATE`, `--plugin-url`): https://github.com/anthropics/claude-code/releases/tag/v2.1.129
