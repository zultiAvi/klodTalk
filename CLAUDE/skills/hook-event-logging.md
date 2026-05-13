---
skill_name: hook-event-logging
triggers:
  - Adding new Claude Code hooks
  - Debugging hook behavior
  - Extending agent observability in KlodTalk
summary: PostToolUse/PostToolUseFailure hooks log tool calls to JSONL; always exit 0.
---

# Skill: Hook Event Logging

## Quick Reference
- Hook script: `server/utils/hooks/post_tool_use_logger.sh`
- Registration: `.claude/settings.json` with `"matcher": ""`
- Rule: hooks MUST exit 0 -- non-zero blocks Claude's tool pipeline
- Logged JSONL fields: `timestamp`, `tool_name`, `duration_ms`, `file_path`, `exit_code`, `effort_level`
- `effort_level` is sourced from `$CLAUDE_EFFORT` (available in hook env since Claude Code v2.1.133+); `null` on older CLIs or when not set

## When to Use
When adding new Claude Code hooks, debugging hook behavior, or extending agent observability in KlodTalk.

## Instructions

### Pattern
PostToolUse and PostToolUseFailure hooks log tool calls to JSONL for per-session observability.

### Key Files
- `server/utils/hooks/post_tool_use_logger.sh` — The hook script (reads stdin JSON, appends JSONL)
- `.claude/settings.json` — Hook registrations

### Hook Script Rules
1. **ALWAYS exit 0** — a non-zero exit blocks Claude's tool pipeline
2. Wrap all logic in `{ ... } 2>/dev/null` block, then `exit 0` at the end
3. Use `jq` for JSON parsing with a raw fallback if jq is unavailable
4. Write to `/workspace/.klodTalk/team/current/hook_events.jsonl`
5. Use `|| true` on every write operation
6. **Exception — enforcement hooks**: hooks that intentionally block a tool call and return feedback to Claude should set `"continueOnBlock": true` on the hook entry (Claude Code v2.1.139+) and exit non-zero with a stderr reason. See `continue-on-block-hooks.md`. The exit-0 rule above still applies to all purely observational hooks.

### Registration Format
Hook groups in `.claude/settings.json` MUST include `"matcher": ""`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "bash /path/to/hook.sh" }
        ]
      }
    ]
  }
}
```

### Adding New Hooks
1. Create a new `.sh` file in `server/utils/hooks/`
2. Follow the exit-0 discipline from `post_tool_use_logger.sh`
3. Register in `.claude/settings.json` with `"matcher": ""`
4. For event-specific hooks, set matcher to the tool name (e.g., `"matcher": "Write"`)

### Environment Variables in Hooks
- `$CLAUDE_EFFORT` — current effort level for the agent invocation. Injected into all hook scripts since Claude Code v2.1.136 (source: https://github.com/anthropics/claude-code/releases/tag/v2.1.136). Capture defensively: `EFFORT="${CLAUDE_EFFORT:-}"` and emit as `null` when empty. Note: hook env is distinct from Bash-tool env — `CLAUDE_CODE_SESSION_ID` is NOT available here (see `session-id-in-bash-tools` skill).
