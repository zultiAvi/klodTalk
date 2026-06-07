---
skill_name: session-start-title
triggers:
  - Adding per-session labels in Claude Code UI/logs
  - Correlating logs across many concurrent agent sessions
  - Reasoning about the SessionStart hook reloadSkills capability
summary: "SessionStart hook returns hookSpecificOutput.sessionTitle to label each Claude Code session (e.g. klodtalk/<project> [<role>]); reloadSkills is now emitted true to trigger a one-time skill-directory rescan during session startup."
---

# Skill: SessionStart Title Hook

## Quick Reference
- Hook script: `server/utils/hooks/session_start_title.sh`
- Registration: `/workspace/.claude/settings.json` under `hooks.SessionStart` with `"matcher": ""`
- Title format: `klodtalk/<KLODTALK_PROJECT> [<KLODTALK_ROLE>]`
- Required Claude Code version: **v2.1.153+** (sessionTitle field)
- Rule: hook MUST exit 0 — non-zero exit blocks Claude's session-start pipeline

## When to Use
When KlodTalk runs many concurrent agent sessions (one per Docker container per role) and operator-side logs need to disambiguate them. Apply this any time you want a human-readable label on a session in Claude Code's UI or transcript exports without changing server code.

## Instructions

### Pattern
Claude Code v2.1.153 added `hookSpecificOutput.sessionTitle` to the SessionStart hook contract. Returning a JSON envelope from the hook script tells the CLI to display that title for the lifetime of the session.

### Hook Output Format
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "sessionTitle": "klodtalk/my-project [coder]",
    "reloadSkills": true
  }
}
```

### Environment Variables Consumed
- `KLODTALK_PROJECT` — project slug (set by `server/run_agent.py` when launching the agent container). Falls back to `"unknown"` if unset.
- `KLODTALK_ROLE` — role tag (e.g. `coder`, `reviewer`, `planner`). Falls back to `"agent"` if unset.

Both env vars are sanitized (control chars stripped, length capped) before being interpolated into the title, since the value is human-facing.

### Registration
`/workspace/.claude/settings.json` (NOT `~/.claude/settings.json` — see `hook-settings-location.md`):
```json
"SessionStart": [
  {
    "matcher": "",
    "hooks": [
      { "type": "command",
        "command": "bash /workspace/server/utils/hooks/session_start_title.sh" }
    ]
  }
]
```

### reloadSkills Field
This script emits `reloadSkills: true` **unconditionally** at session start. SessionStart fires once per container launch (not repeatedly mid-run), so emitting `true` triggers a one-time rescan of the configured skill directories during the CLI's initialization pass. This is always safe and imposes zero extra overhead — it just ensures any skills written to `.claude/skills/` before the container launched are picked up by that session.

Keep the distinction clear:
- **Startup rescan (now active)**: `reloadSkills: true` from SessionStart fires once during initialization. Always safe.
- **Mid-session reload (still un-wired)**: forcing a rescan inside a *running* session would require a live-session signal path (sentinel file, SIGUSR1) that KlodTalk does not yet have. That is a separate future capability, not what this hook does.

### Exit Discipline
Same as all observational hooks: wrap logic in `{ ... } 2>/dev/null` and end with `exit 0`. SessionStart is a startup gate — a non-zero exit would prevent the session from starting at all.

### Graceful Degradation
- If `KLODTALK_PROJECT` / `KLODTALK_ROLE` are unset (non-KlodTalk environments), fall back to the literal strings `unknown` and `agent`.
- If `jq` is missing, build the JSON envelope by hand (safe because env values are sanitized to an ASCII-ish subset before interpolation).
- If the CLI is older than v2.1.153, it ignores the `sessionTitle` field silently; no error is raised.

## Related
- `hook-event-logging.md` — exit-0 discipline, JSONL conventions.
- `hook-settings-location.md` — workspace-level vs user-level settings.json.
- `continue-on-block-hooks.md` — the only category where non-zero exits are intentional.

## Source
Claude Code changelog v2.1.153 — https://releasebot.io/updates/anthropic/claude-code (github.com/anthropics/claude-code via releasebot).
