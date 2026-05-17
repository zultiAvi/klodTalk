---
skill_name: per-user-session-claude-query
triggers:
  - Adding a WebSocket request that derives per-user content from session history via Claude
  - "Summarize", "analyze", "extract", or "explain" features that act on the requesting user's own session view
  - Distinguishing this pattern from session-metadata mutations and from role broadcasts
summary: Direct WebSocket request → owner-gate → filter history → Claude via stdin → unicast result. Cache by `(session_id, user_name)`; invalidate on user-message-count change. Reference handler: `handle_analyze_session` / `handle_summarize_my_requests`.
---

# Skill: Per-User Session-Content Query via Claude

## Quick Reference
- Reference handlers: `handle_analyze_session` and `handle_summarize_my_requests` in `server/server.py` — copy whichever is closer to your feature.
- NOT a broadcast role — do NOT touch `_OUT_MESSAGE_EXCLUDED`, `TEAM_ROLES_SET`, or `out_messages/`.
- NOT session metadata — do NOT touch `_session_to_dict` or the sessions list.
- Result is **unicast** to `connected_clients.get(user_name)`, never broadcast — even when the same session has multiple users.
- Always pipe the prompt to Claude via stdin (`-p "-"`, `input=full_prompt`) per `claude-prompt-stdin-arg-max`.

## When to Use
When the user clicks a session-page button that should produce content derived from the session history but personalized to *them* (their own messages, their own summary, their own analysis perspective). The result must not leak across users.

## The Pattern

### 1. New WebSocket message types (no broadcast wiring)
- Client → server: `{"type": "<verb>_<noun>", "session_id": "..."}`.
- Server → client: `{"type": "<verb>_<noun>_result", "session_id": "...", "status": "running|complete|error", "summary"/"analysis": "...", "cached": true?}`.

### 2. Server handler skeleton (`server/server.py`)
```python
_session_<feature>: dict[tuple[str, str], tuple[str, int]] = {}
_session_<feature>_running: set[tuple[str, str]] = set()

async def handle_<feature>(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"})); return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"})); return
    if user_name != session.user_name:  # owner-only gate — BEFORE history I/O
        await ws.send(json.dumps({"type": "<feature>_result", "session_id": session_id,
                                  "status": "error", "message": "Only the session owner..."}))
        return
    messages = _load_history(session)             # closed → archive jsonl, open → history_store
    user_msgs = [m for m in messages if m.get("role") == "user"]   # filter as needed
    cache_key = (session_id, user_name)
    # ... cache hit / running guard / launch asyncio.create_task(_run_<feature>(...))
```

### 3. Async runner
- Load a static system prompt from `server/prompts/<feature>.md` (server-side constant path — no user input on the path).
- Truncate history at ~100,000 chars defensively.
- Invoke Claude via stdin: `subprocess.run([_CLAUDE_CMD, "--dangerously-skip-permissions", "--output-format", "json", "-p", "-", "--max-turns", "1"], input=full_prompt, capture_output=True, text=True, timeout=120)`.
- Parse `result` field from JSON; fall back to raw stdout on JSONDecodeError.
- Send `complete` ONLY to `connected_clients.get(user_name)`. Silently no-op if the user disconnected.
- `finally: _session_<feature>_running.discard(cache_key)`.

### 4. Dispatcher
Wire `elif msg_type == "<verb>_<noun>": await handle_<feature>(websocket, client_name, msg)` in `handle_client`.

### 5. Web client
- Add a button next to existing per-session buttons (e.g. near the Analyze button).
- Re-use the `.analysis-overlay` CSS class for the result panel — no new CSS needed.
- Render `msg.summary` / `msg.analysis` via `escapeHtml()` (XSS).
- Reset button label/enabled state at the top of the result handler so connection drops don't leave it stuck.

### 6. Android (minimal, optional UI)
- `MsgType.<FEATURE>_RESULT` constant.
- `sendXxx(sessionId)` helper in `WebSocketClient.kt`.
- No-op `when` branch in receive dispatcher to avoid "unknown type" warnings.
- UI is acceptable as a follow-up — match the convention of the most similar existing feature (e.g. Analyze has no Android UI).

## Pitfalls
- Do NOT pass the prompt as an argv string — long histories will exceed `ARG_MAX`. Always stdin.
- Do NOT broadcast `complete` to `session.users` — the content is per-user.
- Do NOT skip the owner-only gate; without per-message author tracking, you cannot safely distinguish whose messages are whose.
- Place the owner check BEFORE the history I/O, otherwise non-owners trigger needless reads before rejection.
- Echoing `str(e)` to the client leaks filesystem paths — log details server-side and return a generic message on exception.
