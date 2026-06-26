---
skill_name: auto-mode-hard-deny
triggers:
  - Defining or hardening a read-only role (reviewer, qa_analyst, validator)
  - Adding a settings-level safety rail beyond `disallowedTools`
  - Reviewing an agent that should never make autonomous writes
summary: `autoMode.hard_deny: true` is a settings-level lock that unconditionally blocks auto mode; pair with `disallowedTools` for defense-in-depth on read-only roles.
---

# Skill: autoMode.hard_deny for Read-Only Roles

## Quick Reference
- Setting key: `autoMode.hard_deny: true` in `.claude/settings.json`
- Effect: blocks auto-mode tool execution regardless of allow rules — cannot be overridden by an allow entry
- Available since: Claude Code v2.1.136
- Recommended targets: `reviewer`, `qa_analyst` (any role intended to be read-only)
- **Do NOT apply to**: `coder`, `planner`, `executor`, `optimizer_code`, or any role that performs writes

## When to Use
- A role's contract is read-only and any autonomous write would be a bug.
- You already use `disallowedTools` and want a settings-level lock as defense-in-depth.

## Instructions

### Important: Placement in KlodTalk
The KlodTalk orchestrator currently parses only `mcpServers:` and `disallowedTools:` from role frontmatter (see `mcp-frontmatter` and `disallowed-tools-frontmatter` skills). A `settings:` block in role frontmatter is **NOT** forwarded to `.claude/settings.json` by `server/run_agent.py` or `teams/run_claude_team.sh`. Adding it to frontmatter is therefore a no-op today.

The correct placement is at the **operator level**, in the agent container's `.claude/settings.json` (the same file edited by `server/run_agent.py` when installing hooks). Example:

```json
{
  "autoMode": {
    "hard_deny": true
  },
  "hooks": { /* existing hook registrations */ }
}
```

When the orchestrator gains native frontmatter parsing for `settings:` (the same forward-looking note that applies to `mcpServers`), the equivalent role-frontmatter form will be:

```yaml
---
settings:
  autoMode:
    hard_deny: true
disallowedTools:
  - Bash
  - Write
  - Edit
  - MultiEdit
  - NotebookEdit
---
```

### Layering
- `disallowedTools` (frontmatter) — enforced in `--print` mode for the role.
- `autoMode.hard_deny` (settings) — locks the container against auto-mode writes regardless of allow rules.
- Use both: one bypassed alone is still caught by the other.

### Cross-References
- `classify-all-shell.md` — the write-capable-role counterpart (`autoMode.classifyAllShell`, CLI 2.1.193): when a hard deny would break the role, classify every shell command instead.

### Source
Claude Code v2.1.136: https://github.com/anthropics/claude-code/releases/tag/v2.1.136 (github.com/anthropics/claude-code, 82,000+ stars). Pattern reinforced by `rohitg00/awesome-claude-code-toolkit` guard/lifecycle hooks (~1,500 stars).
