---
skill_name: session-start-title
triggers:
  - Adding per-session labels in Claude Code UI/logs
  - Correlating logs across many concurrent agent sessions
  - Reasoning about the SessionStart hook reloadSkills capability
summary: "SessionStart hook returns hookSpecificOutput.sessionTitle to label each Claude Code session (e.g. klodtalk/<project> [<role>]); reloadSkills field reserved for future hot-reload."
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
    "reloadSkills": false
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
The same hook payload supports `reloadSkills: true` to force the CLI to rescan the configured skill directories within a live session. This script currently emits `reloadSkills: false` because KlodTalk has no live-session signal path to trigger a reload mid-run; see the deferred ideas entry on `reloadSkills`. When KlodTalk gains a way to signal a running container (sentinel file, SIGUSR1), this hook can branch on the signal and emit `reloadSkills: true` on the next SessionStart event without any other changes.

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
