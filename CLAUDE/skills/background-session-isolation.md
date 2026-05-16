---
skill_name: background-session-isolation
triggers:
  - Background agent appears not to write files to /workspace
  - Disabling a plugin fails with a dependency error
  - Configuring worktree behavior for Docker-mounted agents
summary: How to configure worktree.bgIsolation, handle plugin dependency enforcement, and the PowerShell ExecutionPolicy default added in Claude Code CLI v2.1.143.
---

# Skill: Background Session Isolation (v2.1.143)

## Quick Reference
- Setting: `worktree.bgIsolation` in `.claude/settings.json` (default: isolated)
- Set to `"none"` for KlodTalk Docker agents so writes land in mounted `/workspace`
- `claude plugin disable <X>` now refuses if another enabled plugin depends on `<X>`
- PowerShell tool passes `-ExecutionPolicy Bypass` by default (Windows hosts only)
- Source: Claude Code CLI v2.1.143 CHANGELOG (github.com/anthropics/claude-code)

## When to Use
When a KlodTalk background agent (`claude -p` in a container) appears to "lose" file edits, when `claude plugin disable` errors with a dependency message, or when validating Windows-host PowerShell tool behavior.

## Instructions

### Configuring worktree.bgIsolation
KlodTalk agents run in Docker containers with `/workspace` bind-mounted from the host. The default isolated-worktree mode copies edits into a sandbox that does not survive container exit, so changes appear lost. Set `"worktree": { "bgIsolation": "none" }` in the container's `.claude/settings.json` to let background sessions edit the mounted tree directly.

### Plugin Dependency Enforcement
If `claude plugin disable <X>` fails, another enabled plugin depends on `<X>`. Run `claude plugin list` to identify dependents, disable them first, then retry. Do not force-remove plugin files manually — that bypasses the dependency check and breaks the dependent skill.

### PowerShell ExecutionPolicy (informational)
The PowerShell tool now invokes scripts with `-ExecutionPolicy Bypass` by default, resolving silent permission failures on Windows hosts. Linux-only KlodTalk deployments are unaffected.

## Related
- `CLAUDE/skills/docker-claude-stability.md` — Dockerfile.agent CLI pinning
- `CLAUDE/skills/plugin-prefer-https.md` — plugin install transport

## Source
Claude Code CLI v2.1.143 CHANGELOG — https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
