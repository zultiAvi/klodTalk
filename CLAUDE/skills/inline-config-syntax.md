---
skill_name: inline-config-syntax
triggers:
  - Changing a setting temporarily in a role
  - Setting effort per pipeline stage without editing settings.json
  - Using /config in a role file
  - Avoiding persistent settings.json edits for per-session config
summary: "Since v2.1.181, emit `/config key=value` anywhere in the prompt to change any Claude Code setting for the current session; ephemeral — reverts on session exit, does not write settings.json."
---

# Skill: `/config key=value` Inline In-Session Setting Syntax

## When to Use
When a role needs to change a Claude Code setting for the current session only (e.g. per-stage `effort`) without a persistent edit to `settings.json`. Requires CLI floor **>= 2.1.181** (see `required-minimum-version-pin.md`).

## Instructions
Emit `/config key=value` anywhere in the prompt. Examples:

```
/config model=claude-sonnet-4-6
/config effort=high
/config maxTokens=4096
```

Scope and behavior:
- Applies to the **current session only**; reverts on session exit.
- Does **not** write to `settings.json` — no persistent drift, nothing to clean up.
- Use it instead of editing `settings.json` for any one-off per-stage tweak.

### Embedding in a role
Add a `/config` line as the **first-line instruction** in `teams/roles/<role>.md` so it applies before the role does its work. Practical KlodTalk examples:
- Planner: `/config effort=low` for cheap exploratory decomposition.
- Coder: `/config effort=high` for careful implementation.

### Sub-agent inheritance
Sub-agents spawned within the session **inherit** the overridden setting unless they emit their own `/config` to override it. Set the override at the orchestrator/parent level if you want it to apply pipeline-wide.

## Related
- `required-minimum-version-pin.md` — the 2.1.181 floor this syntax requires.
- `model-version-hygiene.md` — the `effort:` reasoning-level control commonly set this way.

## Source
Claude Code CHANGELOG v2.1.181 — https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (github.com/anthropics)
