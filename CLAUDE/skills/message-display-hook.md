---
skill_name: message-display-hook
triggers:
  - Transforming assistant messages before they reach the WebSocket client
  - Stripping ANSI escape sequences from agent output
  - Injecting stage tags or truncating large messages on the response path
summary: "`MessageDisplay` hook (Claude Code v2.1.152+) fires before an assistant message is shown to the user; return `hookSpecificOutput.updatedMessage` to transform, `{}` to pass through."
---

# Skill: `MessageDisplay` Hook for Assistant-Side Transformations

## Quick Reference
- Event: `MessageDisplay` (assistant message, pre-display)
- CLI requirement: Claude Code v2.1.152+
- Stdin payload: JSON with the full message text
- Output: `{"hookSpecificOutput": {"updatedMessage": "<transformed>"}}` to replace; `{}` to pass through
- Registration: `/workspace/.claude/settings.json` under `hooks.MessageDisplay` with `"matcher": ""`
- Exit discipline: ALWAYS `exit 0` — non-zero would block the response stream

## When to Use
- An agent's output reaches the KlodTalk WebSocket clients (web/Android) with terminal escape sequences that the clients render as raw text — strip them server-side before they hit the wire.
- You want clients to filter or color-code messages by pipeline stage without parsing the body — inject a `[STAGE: <role>]` prefix that clients can split off.
- A Coder agent occasionally emits a very large message (e.g. dumped diff) that floods the WebSocket — truncate above a byte threshold and spill the tail to disk.

## What the Hook Does

1. Reads the `MessageDisplay` JSON payload from stdin (contains the full assistant message text).
2. Applies the configured transformation:
   - **Strip ANSI**: `sed 's/\x1b\[[0-9;]*m//g'` removes terminal color/format escapes.
   - **Inject stage tag**: prepend `[STAGE: coder]` (or `reviewer`, `planner`, ...) so clients can categorize progress.
   - **Truncate and spill**: if the message exceeds a configurable byte threshold (e.g. 64 KB), keep the first N bytes plus `... [truncated, see message_overflow_<ts>.txt]` and write the full body to `/workspace/.klodTalk/team/current/message_overflow_<timestamp>.txt`.
3. Emits the replacement payload (or `{}` for pass-through):
   ```json
   {"hookSpecificOutput": {"hookEventName": "MessageDisplay", "updatedMessage": "<transformed text>"}}
   ```
4. Always `exit 0`.

Complements `post-tool-output-sanitize.md` (which intercepts tool output
*before* Claude reads it). `MessageDisplay` is the symmetric hook on the
*outbound* path — the first hook that can rewrite assistant output on its
way to the user/WebSocket.

## Registration

Per `hook-settings-location.md`, register in
`/workspace/.claude/settings.json` (workspace-level). The hook group object
requires the `matcher` field — use `""` to match all assistant messages:

```json
{
  "hooks": {
    "MessageDisplay": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "bash /workspace/server/utils/hooks/message_display_transform.sh" }
        ]
      }
    ]
  }
}
```

## Exit Discipline

ALWAYS `exit 0`. A non-zero exit would block the response stream to the
WebSocket client — the user would see nothing. Catch all internal errors
and fall through to `{}` (pass-through) rather than failing.

## CLI Version Requirement

`MessageDisplay` was introduced in **Claude Code v2.1.152**. On older CLI
versions the hook is silently ignored — no error, but no transformation.
Confirm with `claude --version` inside the agent container before relying
on it.

## Verifying

After registering the hook, send a request that produces an ANSI-coloured
response and inspect the WebSocket frame:

```bash
echo '{"message":"\u001b[31mERROR\u001b[0m: failed"}' \
  | bash /workspace/server/utils/hooks/message_display_transform.sh
```

Expected stdout:

```json
{"hookSpecificOutput": {"hookEventName": "MessageDisplay", "updatedMessage": "ERROR: failed"}}
```

## Related
- `post-tool-output-sanitize.md` — the inbound (pre-Claude) counterpart.
- `hook-settings-location.md` — workspace-level settings file.
- `hook-event-logging.md` — exit-0 discipline and matcher requirement.
- `large-output-spill.md` — analogous size-cap pattern for tool output.
- `terminal-sequence-hook-output.md` — ANSI handling primer.

## Source
- anthropics/claude-code v2.1.152 release notes —
  https://github.com/anthropics/claude-code/releases (May 27 2026).
