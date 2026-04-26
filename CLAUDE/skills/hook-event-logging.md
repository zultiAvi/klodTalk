# Skill: Hook Event Logging

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
