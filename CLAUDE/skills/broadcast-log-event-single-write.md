---
skill_name: broadcast-log-event-single-write
triggers:
  - Adding a new `_broadcast_to_session_users` call site in `server/server.py`
  - Diagnosing duplicated messages appearing after closing+reopening a session
  - Reviewing whether a lifecycle/error broadcast persists into events.jsonl
summary: "`_broadcast_to_session_users` has a keyword-only `log_to_session: bool = False` gate; pass `True` ONLY when there is no peer `session_log.log_event(...)` for the same content in the surrounding lines, otherwise events.jsonl will double-write and reopened sessions show duplicates."
---

# Skill: `_broadcast_to_session_users` Single-Write Contract

## Quick Reference
- Function: `server/server.py:_broadcast_to_session_users(session_id, payload, *, log_to_session: bool = False)`
- Default `log_to_session=False` -> the mirror block into `session_log.log_event(...)` is SKIPPED.
- Pass `log_to_session=True` ONLY when no peer `session_log.log_event(...)` exists in the surrounding ~30 lines.
- Wrong default at one call site -> duplicate lines in `/tmp/klodTalk/logs/<sid>.klodTalk/events.jsonl` -> duplicated messages on reconnect to a closed session.

## When to Use
- Authoring a new handler that broadcasts a `new_message`, `session_*`, or error payload.
- Reviewing a PR that adds a `_broadcast_to_session_users(` call.
- Investigating "messages appear twice after I reopen the session" bug reports.

## Decision Table

| Call-site pattern | log_to_session= | Why |
|-------------------|-----------------|-----|
| Handler logs explicitly with `session_log.log_event(sid, role, content, ...)` then broadcasts the same content | **False** (default) | Avoid double-write; explicit log already persisted. |
| Lifecycle broadcast (e.g. `session_working`, `session_reopened`, nightly start/stop, model-references-updated) with NO peer `log_event` for the same content | **True** | The broadcast is the only path to persistence; mirror keeps the safety net. |
| Error broadcast emitted via `_broadcast_to_session_users` without an accompanying explicit `log_event` | **True** | Same reason — preserve durable record of the error. |
| Legacy backward-compat second broadcast of content already broadcast as `new_message` (e.g. legacy `{"type":"response", ...}` at server.py:1281) | **False** | The content was already persisted via the paired primary broadcast's peer `log_event`. A third write is pure duplication. |

## How to Audit a New Call Site
1. Grep upward ~30 lines from the broadcast for `session_log.log_event(`.
2. If a peer call exists AND its `content` argument matches the broadcast payload's user-visible body -> default `False`.
3. If no peer exists, OR the peer logs a DIFFERENT string (e.g. internal status vs user-facing summary) -> pass `log_to_session=True` AND add a one-line comment noting why.
4. Verify with `git grep -n "_broadcast_to_session_users(" server/server.py` and confirm your new site is the only addition.

## Regression Test
`tests/test_session_log.py:test_broadcast_does_not_double_write_when_log_to_session_false` pins the contract: explicit `log_event` + default-arg `_broadcast_to_session_users` -> exactly one line in events.jsonl. If you change the default behavior, this test must be updated and the rationale recorded in `instincts.md`.

## Sibling Concern: Hook Events in `_session_to_dict`
`role == "hook"` events are filtered out of `_session_to_dict`'s `messages` list and `handle_reopen_session`'s `session_replay` payload — they stay in `events.jsonl` for debugging but are not surfaced to clients. The archive-branch path in `_session_to_dict` (when `persistent` is empty and `status == "closed"`) currently lacks this filter; if hook events ever appear in archived `session.jsonl`, they will leak from that path.
