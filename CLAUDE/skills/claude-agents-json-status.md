---
skill_name: claude-agents-json-status
triggers:
  - Authoring a multi-agent pipeline role that needs to check whether a sub-agent is still running
  - Diagnosing a Claude Code session that appears stuck or hung
  - Building a status reporter / watchdog utility for KlodTalk pipeline runs
summary: "Use `claude agents --json` (Claude Code v2.1.145+) to query live session state machine-readably instead of inferring it from in_message.txt/out_message.txt file writes."
---

# Skill: `claude agents --json` Session-State Polling

## Quick Reference
- Command: `claude agents --json` -- emits JSON array of live sessions.
- Scope to a project: `claude agents --json --cwd /workspace`.
- Fields per session: `sessionId`, `status`, `model`, `cwd`, `parentSessionId`, `elapsed`.
- OTEL spans expose the same identity via `agent_id` / `parent_agent_id` (v2.1.145).
- Requires Claude Code >= v2.1.145; the `--cwd` flag landed in v2.1.141.

## When to Use
Use this skill when an Orchestrator or watchdog role needs a deterministic, lower-latency answer to "is sub-agent X still running?" than the current file-write inference (waiting for `out_message.txt` to update). Also use it when assembling a status reporter, when diagnosing a stuck session, or when correlating OTEL traces to KlodTalk sessions.

## Instructions

### Listing live sessions
```bash
claude agents --json                       # all sessions
claude agents --json --cwd /workspace      # scope to one project tree
```
Parse the JSON with `jq` -- example: `claude agents --json | jq '.[] | select(.status=="running") | .sessionId'`.

### Output schema (v2.1.145)
- `sessionId` -- string, matches the `session_id` used in WebSocket messages.
- `status` -- `running` | `idle` | `exited` | `error`.
- `model` -- e.g. `claude-opus-4-7`.
- `cwd` -- absolute path the session was launched with.
- `parentSessionId` -- nullable; set for sub-agents dispatched via `claude agents`.
- `elapsed` -- seconds since session start.

### Dispatch-time overrides (v2.1.142)
Complementary flags for `claude agents <subcommand>`: `--add-dir`, `--settings`, `--mcp-config`, `--model`, `--effort`. Useful when launching a sub-agent with a different model or MCP config than the parent.

### Hook integration snippet
A Stop or PostToolUse hook can ring a terminal bell when the last sub-agent under a parent exits:
```bash
remaining=$(claude agents --json --cwd "$CLAUDE_PROJECT_DIR" \
  | jq "[.[] | select(.parentSessionId==\"$PARENT_ID\" and .status==\"running\")] | length")
if [ "$remaining" = "0" ]; then printf '\a'; fi
```
Emit the bell via the `terminalSequence` hook output -- see `terminal-sequence-hook-output.md`.

### OTEL correlation
The `agent_id` and `parent_agent_id` span fields (v2.1.145) match the JSON `sessionId` / `parentSessionId` -- use them to join Claude Code traces with KlodTalk's per-session logs.

## Related
- `session-id-in-bash-tools.md` -- propagating the same session identifier into agent bash environments.
- `terminal-sequence-hook-output.md` -- emitting the bell / notification from a hook.
- `claude-agents-cli.md` -- broader `claude agents` subcommand reference.

## Source
Claude Code v2.1.145 release notes -- https://github.com/anthropics/claude-code/releases/tag/v2.1.145 (github.com/anthropics/claude-code).
