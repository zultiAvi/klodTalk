---
skill_name: hook-comma-matcher-syntax
triggers:
  - Writing a new Claude Code hook entry and deciding what to put in its `matcher` field
  - A tool-specific hook in `settings.json` never fires even though the command path is correct
  - Reviewing a KlodTalk hook that uses a comma-separated tool list like `"Bash,Edit"`
summary: 'Hook `matcher` accepts `""` (all tools/any event) or a comma-separated tool list (e.g. `"Bash,Edit,MultiEdit"`); comma-separated matchers silently no-oped before CLI 2.1.191 and work from 2.1.191 (KlodTalk''s floor) onward — keep `""` for KlodTalk''s existing all-tool hooks, use a comma-list only for genuinely tool-specific hooks.'
---

# Skill: Hook `matcher` Comma-Separated Tool Syntax

## Quick Reference
- `"matcher": ""` — matches **all tools / any event** (the value every KlodTalk hook uses today; correct, keep it).
- `"matcher": "Bash,Edit,MultiEdit"` — matches **only** those named tools (comma-separated, no spaces needed).
- Pre-2.1.191 footgun: a comma-separated matcher **silently matched nothing** — the hook never fired and produced no error.
- From **CLI 2.1.191** onward (KlodTalk's pinned floor) comma-separated matchers work as documented.

## When to Use
Whenever you add a hook entry to `/workspace/.claude/settings.json` and need to decide
the `matcher` value, or when debugging a tool-specific hook that "never runs."

## The Fix (2.1.191)
Before v2.1.191, only a single tool name or `""` matched; a comma list like
`"Bash,Edit"` was parsed as one literal tool name that never existed, so the hook
no-oped silently. v2.1.191 fixes the parser so each comma-separated entry is matched
individually. KlodTalk's CLI floor is now 2.1.191 (see `required-minimum-version-pin.md`),
so the documented syntax is safe to rely on.

## KlodTalk Convention
- Keep `""` for the existing all-tool hooks — every current KlodTalk hook
  (`PostToolUse`, `PostToolUseFailure`, `SessionStart`, `SubagentStart`/`SubagentStop`,
  `MessageDisplay`, `PostSession`, `PreCompact`, `PostCompact`) uses `""` and that is
  correct: they intentionally cover all tools/events.
- Use a comma-list (e.g. `"Bash,Write"`) **only** for a genuinely tool-specific hook —
  e.g. a future guard that should run solely for file-mutating tools. Do not narrow an
  existing all-tool hook to a comma-list without a deliberate reason.

## Cross-References
- `hook-settings-location.md` — register hooks in `/workspace/.claude/settings.json`, not `~/.claude/settings.json`.
- `required-minimum-version-pin.md` — the 2.1.191 floor that makes comma-separated matchers reliable.
