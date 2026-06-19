---
skill_name: attribution-session-url
triggers:
  - Agent commit or PR messages are appending a claude.ai session link you don't want
  - Configuring how Claude Code attributes its autonomous commits/PRs
  - Hardening the nightly-scout bot's commit hygiene
summary: "Set `attribution.sessionUrl: false` in `.claude/settings.json` (Claude Code >= 2.1.183) to suppress the claude.ai session link Claude Code otherwise appends to agent-authored commit and PR messages."
---

# Skill: attribution.sessionUrl Setting

## When to Use
When agent-authored commits or PRs should NOT carry a `claude.ai` session URL in their
message footer. KlodTalk's nightly-scout bot commits unattended and the link is noise
(the session is internal and not shareable), so KlodTalk pins it `false`. Requires
CLI floor **>= 2.1.183** (see `required-minimum-version-pin.md`).

## Instructions
Add the `attribution` block to `/workspace/.claude/settings.json` (top-level key):

```json
{
  "attribution": {
    "sessionUrl": false
  }
}
```

Behavior:
- `false` — Claude Code omits the `claude.ai` session-link line from commit/PR messages.
- `true` / omitted — the link is appended (default upstream behavior).
- It only governs the auto-generated session URL; it does NOT touch the
  `Co-Authored-By:` trailer or any message body the agent writes itself.
- Lives in the workspace-level settings file that `run_agent.py` mounts as operator
  settings; older CLIs (< 2.1.183) silently ignore the unknown key.

## Related
- `required-minimum-version-pin.md` — the 2.1.183 floor this setting requires.
- `hook-settings-location.md` — why this goes in the workspace-level settings file.

## Source
Claude Code release v2.1.183 — https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (anthropics/claude-code)
