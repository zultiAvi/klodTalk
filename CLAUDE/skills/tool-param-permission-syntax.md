---
skill_name: tool-param-permission-syntax
triggers:
  - Constraining which model a sub-agent role may select at the permission-rule level
  - Gating Bash calls by command prefix in a role's permission rules
  - Writing allow/deny permission rules that match on a tool parameter, not just the tool name
summary: "Claude Code (>= 2.1.178) supports `Tool(param:value)` permission-rule syntax — allow/deny rules can match a specific tool parameter (e.g. `Agent(model:claude-opus-4-8)`, `Bash(command:git*)`), giving per-parameter least-privilege beyond whole-tool denylists. Doc/config only — no server logic."
---

# Skill: Tool(param:value) Permission-Rule Syntax

## Quick Reference
- Syntax: `Tool(param:value)` in a permission `allow`/`deny`/`ask` list — matches calls
  where tool `Tool` has parameter `param` equal to (or prefix-matching) `value`.
- Requires Claude Code **>= 2.1.178** (KlodTalk pins this floor — see `required-minimum-version-pin.md`).
- Trailing `*` is a prefix glob: `Bash(command:git*)` matches any Bash call whose
  command starts with `git`.
- Complements `disallowedTools:` (whole-tool denylist): this matches on a *parameter value*,
  not just the tool name.

## When to Use
- A role may use a tool but only with restricted parameter values (e.g. allowed to run
  `git` but nothing else; allowed to spawn sub-agents but only at Sonnet/Haiku, never Opus).
- You want a harness-level hard block on an expensive or unsafe parameter value rather than
  relying on prompt instructions the model might ignore.

## KlodTalk Examples

### Block Opus-level sub-agents in cost-sensitive roles
A reviewer or scout role that should never spawn an Opus-tier sub-agent:
```yaml
---
permissions:
  deny:
    - Agent(model:claude-opus-4-8)
---
```
This is the permission-rule complement to `enforceAvailableModels` (which constrains the
*allowlist*); use it per-role when only *some* roles should be barred from Opus.

### Gate Bash by command prefix
An executor role allowed to run git but nothing else:
```yaml
---
permissions:
  allow:
    - Bash(command:git*)
  deny:
    - Bash
---
```

## KlodTalk Runtime Caveat — `permissions:` is NOT wirable per-role today
**Do not add a `permissions:` block to `teams/roles/*.md` frontmatter — it is a dead no-op.**
Verified 2026-06-17 (file:line evidence):
- KlodTalk code parses/forwards only `mcpServers` and `disallowedTools` from role
  frontmatter (project instinct #7). A grep for `disallowedTools` across `server/` +
  `teams/` matches **only** role `.md` files and one hook comment — it appears in **no**
  executable path. `permissions:` has no parser/sink at all and would be silently dropped
  (same no-op class as the `settings:` key documented in `auto-mode-hard-deny.md`).
- The team orchestrator spawns sub-agents via the **native Agent tool**, which accepts a
  `disallowedTools` parameter but does **NOT** accept a `permissions` parameter — there is
  no place to forward a param-scoped deny even if it were parsed.
- Both launch paths run with `--dangerously-skip-permissions`
  (`teams/run_claude_team.sh:240`, `server/run_agent.py:300`), which bypasses the
  `permissions` allow/ask/deny engine entirely.
- **Net:** `Tool(param:value)` deny rules cannot currently be enforced per-role in KlodTalk
  without a runtime change (a parser to forward `permissions:` into the Agent tool call AND
  dropping `--dangerously-skip-permissions` for that spawn). Until then, restrict roles via
  the `disallowedTools` whole-tool denylist and constrain models globally via
  `enforceAvailableModels` (`enforce-available-models.md`).

## Notes
- This is parameter-level, role-scoped. The model allowlist (`enforceAvailableModels`) is
  global; `Tool(param:value)` deny rules are how you tighten a *single* role below the
  global allowlist.
- Applying concrete `Agent(model:...)` rules to specific KlodTalk role files (reviewer.md,
  executor.md) is a follow-on per-role analysis — and per the runtime caveat above it is
  blocked on a runtime change, not a frontmatter edit.

## Cross-References
- `required-minimum-version-pin.md` — the 2.1.178 floor that enables this syntax.
- `enforce-available-models.md` — the global model allowlist this per-role syntax tightens.
- `disallowed-tools-frontmatter.md` — the whole-tool denylist this parameter-level syntax complements.

## Source
- Claude Code CHANGELOG v2.1.178 (`Tool(param:value)` permission-rule syntax) —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (code.claude.com, 2026-06-15)
