---
skill_name: skill-overrides-per-role
triggers:
  - Restricting which skills a role (reviewer, validator, qa_analyst) may invoke
  - Hardening read-only roles beyond `disallowedTools`
  - Defining role-level skill access policy for a KlodTalk team
summary: `skillOverrides` (Claude Code v2.1.129+) restricts skill invocation per-role via three modes (`off`, `user-invocable-only`, `name-only`); pair with `disallowedTools` for layered access control on read-only roles.
---

# Skill: skillOverrides for Per-Role Skill Access

## Quick Reference
- Setting key: `skillOverrides` in `.claude/settings.json` (or, eventually, role frontmatter)
- Available since: Claude Code v2.1.129
- Modes:
  - `off` — skills disabled entirely for this scope
  - `user-invocable-only` — only the user (not Claude autonomously) can trigger skills
  - `name-only` — Claude sees skill names but not full skill content until explicitly invoked
- Recommended targets: `reviewer`, `validator`, `qa_analyst` (read-only / analysis roles)

## When to Use Each Mode
- **`off`**: a role must never invoke any skill (strictest; use for pure validators).
- **`user-invocable-only`**: prevents Claude from auto-triggering skills mid-pipeline (good for reviewers — keeps reviews deterministic).
- **`name-only`**: reduces context pressure when many skills exist but few are relevant; Claude can ask to load a specific skill by name.

## Instructions

### Example Frontmatter (Reviewer Role)
```yaml
---
skillOverrides: user-invocable-only
disallowedTools:
  - Bash
  - Write
  - Edit
  - MultiEdit
  - NotebookEdit
---
```

### Caveat: KlodTalk Orchestrator Limitation (today)
Per `.klodTalk/instincts.md`, the KlodTalk orchestrator currently forwards **only** `mcpServers:` and `disallowedTools:` from role YAML frontmatter to the agent runtime. A `skillOverrides:` key in frontmatter is **silently ignored** today — it is a no-op until orchestrator support lands.

**Workaround (today)**: enforce `skillOverrides` at the container level by writing it into `.claude/settings.json` directly (the same file edited by `server/run_agent.py` for hook installation). Example:
```json
{
  "skillOverrides": "user-invocable-only",
  "autoMode": { "hard_deny": true }
}
```

**Future**: when the orchestrator gains frontmatter parsing for additional keys (same forward-looking note that applies to `settings:` and `autoMode`), `skillOverrides` in role frontmatter will become the canonical placement.

### Layering
- `disallowedTools` — blocks specific tools (Bash, Write, Edit, ...).
- `skillOverrides` — restricts skill invocation independent of tool gating.
- `autoMode.hard_deny` — settings-level lock against auto-mode writes.
- Use together for defense-in-depth on read-only roles.

### Source
Claude Code v2.1.129 release notes: https://github.com/anthropics/claude-code/releases/tag/v2.1.129 (github.com/anthropics/claude-code). Published 2026-05-06.
