---
skill_name: add-session-metadata-field
triggers:
  - Adding a new field to the Session dataclass (e.g. tags, status, priority, due date)
  - Adding a WebSocket message that mutates session metadata
  - Wiring server-side session metadata to web + Android clients
summary: New Session-level metadata needs edits in 5 specific places — Session dataclass + setter, server.py `_session_to_dict` + handler + dispatcher, both clients' parsers/UI. Use `add_user_to_session` as the canonical reference pattern.
---

# Skill: Add a New Session Metadata Field

## Quick Reference
- Reference handler: `handle_add_user_to_session` / `session_user_added` in `server/server.py` — copy this pattern.
- This is NOT an agent-emitted broadcast role — do NOT touch `_OUT_MESSAGE_EXCLUDED`, `TEAM_ROLES_SET`, or `out_messages/` files.
- The `broadcast-message-file-handler` skill is for ROLE files (agent output); this skill is for METADATA mutations (direct WebSocket messages).

## When to Use
When adding any persisted, client-editable session-level field: tags, comments, status, owner, priority, due date, color, pinned, archived. Not for agent output and not for transient per-message data.

## The 5-Place Pattern

### 1. `server/session_manager.py` — Session dataclass + setter
- Add the field with a safe default (`field: str = ""`, `tags: list = field(default_factory=list)`).
- `Session(**v)` in `load_sessions` is backward-compatible thanks to the default — old `sessions.json` records load fine.
- Add a setter method modeled on `add_user_to_session`:
  ```python
  def set_session_<field>(self, session_id: str, value: <Type>) -> bool:
      session = self._sessions.get(session_id)
      if session is None: return False
      # defensive coercion + truncation
      session.<field> = <sanitized_value>
      self.save_sessions()
      return True
  ```

### 2. `server/server.py:_session_to_dict`
Add `"<field>": getattr(session, '<field>', <default>)`. Every place that emits a session (history, sessions list, session_created) auto-picks up the field — no other change in those paths.

### 3. `server/server.py` — handler + dispatcher
Model on `handle_add_user_to_session` (~L1989):
- Read `session_id` and value from payload with safe defaults.
- Permission gate: `if user_name not in session.users` → send error, return.
- Call the setter.
- Broadcast `{"type": "session_<field>_updated", "session_id": ..., "<field>": ..., "updated_by": user_name}` to **every** connected user in `session.users` (loop pattern from `handle_add_user_to_session` L2036-2046 — wrap each send in try/except).
- Wire `elif msg_type == "set_session_<field>":` in the `handle_client` dispatcher (~L2886).

### 4. Web client (`clients/web/index.html`)
- `_session_to_dict` populates `sessions[id].<field>` automatically; no ingestion change.
- Add a dispatcher `case 'session_<field>_updated':` that updates the cache and re-renders.
- Render in `renderSessionsList` and/or the history topbar.
- For editable fields: use `esc()` for any text rendering (XSS), and implement anti-clobber (see `anti-clobber-focused-input` skill).

### 5. Android client
Five files (no shortcuts):
- `network/MsgType.kt` — `const val SESSION_<FIELD>_UPDATED = "session_<field>_updated"`.
- `network/WebSocketClient.kt` — `SessionInfo.<field>` with default, `parseSession` (use `optString`/`optInt`/etc.), listener method, `when` branch, send helper.
- `viewmodel/MainViewModel.kt` — implement listener method (`.copy(<field> = ...)` on `_sessions`), add public setter.
- `ui/screens/HistoryScreen.kt` and/or `SessionsScreen.kt` — UI + state. Apply anti-clobber for editable fields.

## Verification
- Load an old `sessions.json` (without the field) — must deserialize with the default.
- Set the value as user A; user B sharing the session must see the broadcast.
- Restart server — value persists.
