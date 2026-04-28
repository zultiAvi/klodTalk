# Skill: Hook Events Bypass the Session Log Funnel

## When to Use
When wiring a new event source into per-session logging, when reviewing why some payloads land in `events.jsonl` and others don't, or when debugging "log noise" complaints in the chat replay.

## Instructions

The general `session-log-funnel` rule says every user-visible event MUST land in `/tmp/klodTalk/<id>.klodTalk/events.jsonl` via `session_log.log_event`. **Hook events are the exception.**

### Why hooks are different
- Frequency: one hook fires per tool call (potentially hundreds per session).
- Signal: hook payloads are debug telemetry, not conversation. They have no value in the user's chat replay.
- Replay path: anything written to `events.jsonl` is replayed by `handle_reopen_session` and rendered in the chat list. Hook entries flood the UI.

### Pattern
- Hook events go to `<session_log_dir>/hook_events.jsonl` via `session_log.append_hook_event(session_id, line)`.
- They DO NOT go through `session_log.log_event` and DO NOT enter `events.jsonl` / `log.txt`.
- The watcher in `server/server.py` (~line 1258) tails `<workspace>/.klodTalk/team/current/hook_events.jsonl` and forwards each new line to `append_hook_event`. Offset bookkeeping breaks before advancing on failure so failed lines are retried next poll.
- The web UI (`clients/web/index.html`) carries a defensive `if (msg.role === 'hook') return;` guard plus a filter on history load — so legacy sessions whose `events.jsonl` already contains stray hook rows still render cleanly.

### Decision rule for new event sources
Ask: "Would the user benefit from seeing this in the chat replay?"
- **Yes** → use `session_log.log_event(session_id, role, content)`.
- **No, it's debug telemetry** → write to a sibling file in the same per-session dir, following the `append_hook_event` pattern (try/except, never raises, atomic append).

### Files to know
- `server/session_log.py` — `log_event` (user-visible) vs `append_hook_event` / `append_raw` (debug sinks).
- `server/server.py` watcher — tails workspace files and routes them to the right sink.
- `clients/web/index.html` — defensive filter for `role === 'hook'`.

### Regression test
After any change to the watcher or `session_log`, grep for `log_event\([^)]*hook` — must be zero matches. Reverting that swap re-pollutes the chat replay.
