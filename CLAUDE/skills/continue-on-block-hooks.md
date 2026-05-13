---
skill_name: continue-on-block-hooks
triggers:
  - Writing a PostToolUse hook that should block a tool call and return feedback
  - Migrating an existing "always exit 0" enforcement hook
  - Adding policy-feedback hooks to a KlodTalk agent container
summary: `continueOnBlock: true` (Claude Code v2.1.139+) lets a PostToolUse hook block a tool call and feed the rejection reason back to Claude without halting the session — the modern alternative to the legacy "always exit 0" workaround for enforcement hooks.
---

# Skill: continueOnBlock for PostToolUse Hooks

## Quick Reference
- Setting key: `"continueOnBlock": true` on a PostToolUse hook entry in `.claude/settings.json`
- Available since: Claude Code v2.1.139
- Effect: a non-zero hook exit blocks the tool call but feeds the hook's stderr back to Claude as feedback instead of killing the session
- Pair with: a clear stderr message explaining WHY the call was blocked (Claude will read it)

## When to Use
- The hook's purpose is **enforcement** (policy gate, path guard, secret scanner) — i.e., the hook genuinely wants to refuse a tool call and have Claude react.
- The hook is purely observational (logging, metrics): **do NOT** set `continueOnBlock`; keep the existing "always exit 0" discipline from `hook-event-logging`.

## Instructions

### Registration Snippet
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "continueOnBlock": true,
        "hooks": [
          { "type": "command", "command": "bash /path/to/path_guard.sh" }
        ]
      }
    ]
  }
}
```

### Hook Script Behavior
- Exit 0: allow the tool call (normal pass-through).
- Exit non-zero: block the tool call. Write a short, actionable reason to stderr — Claude receives this as feedback (e.g., `echo "Refused: writes outside /workspace are not permitted" >&2`).
- Without `continueOnBlock`, a non-zero exit historically killed the session — that constraint is what the legacy "always exit 0" rule was guarding against.

### Cross-Reference
- See `hook-event-logging.md` for the legacy exit-0 discipline (still correct for purely observational hooks).
- See `.klodTalk/instincts.md` — the exit-0 instinct is qualified: still applies UNLESS `continueOnBlock: true` is set.

### Source
Claude Code v2.1.139 release notes: https://github.com/anthropics/claude-code/releases/tag/v2.1.139 (github.com/anthropics/claude-code). Published 2026-05-11.
