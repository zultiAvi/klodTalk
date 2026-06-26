---
skill_name: classify-all-shell
triggers:
  - Hardening a write-capable role (coder, executor, planner) that runs autonomous Bash
  - Adding a settings-level shell-safety rail where a hard deny would break the role
  - Routing every shell command through the auto-mode classifier, not just suspicious ones
summary: "`autoMode.classifyAllShell: true` (CLI 2.1.193) routes ALL Bash/PowerShell through the auto-mode safety classifier, not just arbitrary-code patterns; an operator-level `.claude/settings.json` rail for write-capable roles where `autoMode.hard_deny` cannot apply."
description: "Documents the autoMode.classifyAllShell settings key added in Claude Code CLI 2.1.193, which sends every Bash and PowerShell command through the auto-mode safety classifier instead of only the arbitrary-code-execution patterns classified before. Use when hardening a write-capable KlodTalk role (coder, executor, planner) that runs unattended shell, when you want a classify-every-command rail that complements but differs from autoMode.hard_deny, or when deciding where shell-safety settings belong in the agent container."
---

# Skill: autoMode.classifyAllShell for Write-Capable Roles

## Quick Reference
- Setting key: `autoMode.classifyAllShell: true` in `.claude/settings.json`
- Effect: routes **all** Bash/PowerShell commands through the auto-mode classifier, not just arbitrary-code-execution patterns
- Available since: Claude Code **v2.1.193** (floor pinned — see `required-minimum-version-pin.md`)
- Recommended targets: `coder`, `executor`, `planner`, `optimizer_code` — write-capable roles where `autoMode.hard_deny` would break the role
- Contrast: `hard_deny` = unconditional block (read-only roles); `classifyAllShell` = classify-every-command (write-capable roles)

## When to Use
- A role must run shell autonomously, so a hard deny is not an option, but you still want every command (not only suspicious-looking ones) screened by the safety classifier.
- You already use `disallowedTools` / `autoMode.hard_deny` for read-only roles and want the write-capable analogue.

## Placement in KlodTalk
Same constraint as `auto-mode-hard-deny.md`: the orchestrator forwards only `mcpServers:` and `disallowedTools:` from role frontmatter (instinct #7/#39). A `settings:` block in role frontmatter is a **no-op** today. Put it at the **operator level** in the agent container's `.claude/settings.json`:

```json
{
  "autoMode": { "classifyAllShell": true }
}
```

## CAVEAT — skip-permissions
KlodTalk launches `run_agent.py` / `run_claude_team.sh` with `--dangerously-skip-permissions`, which bypasses the permission engine (instinct #39, see `tool-param-permission-syntax.md`). If the classifier is similarly bypassed under skip-permissions, this setting is **forward-looking / no-op today** — mirror the same caveat in `auto-mode-hard-deny.md` and the 2.1.186 named-subagent note. **Verify it is active before relying on it.**

## Cross-References
- `auto-mode-hard-deny.md` — the read-only-role counterpart (`autoMode.hard_deny`).
- `required-minimum-version-pin.md` — the 2.1.193 floor this setting requires.
- `tool-param-permission-syntax.md` — the `--dangerously-skip-permissions` bypass caveat.

## Source
- Claude Code CHANGELOG v2.1.193 — https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md (github.com/anthropics/claude-code, official, 82,000+ stars).
