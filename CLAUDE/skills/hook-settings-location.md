---
skill_name: hook-settings-location
triggers:
  - Documenting where to register a new Claude Code hook in a KlodTalk agent container
  - Reviewing a skill that suggests `~/.claude/settings.json` for hook registration
  - Diagnosing a hook that "disappears" after a container restart
summary: Register hooks in `/workspace/.claude/settings.json`, NOT `~/.claude/settings.json` — `run_agent.py:_setup_agent_hooks()` overwrites the user-level `hooks` key on every container start.
---

# Skill: Where to Register a Claude Code Hook in KlodTalk

## Quick Reference
- Safe path: `/workspace/.claude/settings.json` (workspace-level, persisted)
- Unsafe path: `~/.claude/settings.json` (user-level, clobbered on every container start)
- Reason: `server/run_agent.py:_setup_agent_hooks()` performs `settings["hooks"] = { ... }` on the user-level file every time the agent starts, replacing any operator-added hook entries.

## When to Use
Any skill or operator-facing doc that tells someone where to add a hook entry must point at the workspace-level settings file. If you see `~/.claude/settings.json` recommended for hook registration in a KlodTalk context, treat it as a bug.

## Why
- `_setup_agent_hooks()` installs KlodTalk's built-in PreToolUse / Stop hooks by **fully overwriting** the `hooks` key under `~/.claude/settings.json`. Other settings in that file are preserved, but the `hooks` key is not.
- `/workspace/.claude/settings.json` is read by the Claude Code CLI and is part of the mounted workspace, so operator-added hook entries survive container restarts and ride along with the project.

## Pattern (registering a new hook)
```json
// /workspace/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash /workspace/server/utils/hooks/sanitize_bash_output.sh" }
        ]
      }
    ]
  }
}
```

## Related
- `hook-event-logging.md` — exit-0 discipline and matcher requirements.
- `post-tool-output-sanitize.md` — the skill whose registration section first surfaced this gotcha.
